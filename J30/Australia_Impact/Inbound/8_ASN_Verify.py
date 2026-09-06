import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env
from Australia_Impact.Inbound.Inbound_payload_generation.ASN_Verify_Payload import (
    ASN_Verify_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ASN_Verify_CheckOut_Release:
    @staticmethod
    def _collect_yard_error_codes(response_data: dict) -> set[str]:
        try:
            messages = (
                response_data.get("messages", {})
                .get("Message", [])
            )
            codes = set()
            for item in messages:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("Code", "")).strip() or str(item.get("ErrorCode", "")).strip()
                if code:
                    codes.add(code)
            message_key = str(response_data.get("messageKey", "")).strip()
            if message_key:
                codes.add(message_key)
            return codes
        except Exception:
            return set()

    @classmethod
    def _post_step_detailed(cls, url: str, headers: dict, payload, step_name: str, context: str) -> dict:
        result = {"success": False, "response": None, "status_code": None, "error_codes": set()}
        try:
            response = requests.post(url=url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json() if response.text else {}
            logging.info(f"{step_name} succeeded for {context}.")
            result["success"] = True
            result["response"] = response_data
            return result
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"{step_name} failed for {context}: {http_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
            if http_err.response is not None:
                result["status_code"] = http_err.response.status_code
                logging.error(f"Status code: {http_err.response.status_code}")
                logging.error(f"Response content: {http_err.response.text}")
                try:
                    response_data = http_err.response.json()
                    result["response"] = response_data
                    result["error_codes"] = cls._collect_yard_error_codes(response_data)
                except Exception:
                    pass
        except requests.exceptions.RequestException as req_err:
            logging.error(f"{step_name} request failed for {context}: {req_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except json.JSONDecodeError:
            logging.error(f"{step_name} returned non-JSON response for {context}.")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except Exception as ex:
            logging.error(f"Unexpected error during {step_name} for {context}: {ex}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        return result

    @classmethod
    def _post_checkout_with_fallback(cls, url: str, headers: dict, payload: dict, context: str) -> dict:
        first = cls._post_step_detailed(url, headers, payload, "Check Out", context)
        if first.get("success"):
            return first

        if "YRD::228" not in (first.get("error_codes") or set()):
            return first

        fallback_payload = dict(payload)
        fallback_payload["VisitType"] = "DROP_UNLOAD"
        fallback_payload["TrailerStatus"] = "IB UnLoaded"
        logging.warning(
            f"Retrying Check Out for {context} with fallback payload "
            "(VisitType=DROP_UNLOAD, TrailerStatus=IB UnLoaded) due to YRD::228."
        )
        second = cls._post_step_detailed(url, headers, fallback_payload, "Check Out (Fallback)", context)
        if second.get("success"):
            return second
        return first

    @staticmethod
    def _post_step(url: str, headers: dict, payload, step_name: str, context: str) -> dict | None:
        try:
            response = requests.post(url=url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json() if response.text else {}
            logging.info(f"{step_name} succeeded for {context}.")
            return response_data
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"{step_name} failed for {context}: {http_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
            if http_err.response is not None:
                logging.error(f"Status code: {http_err.response.status_code}")
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"{step_name} request failed for {context}: {req_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except json.JSONDecodeError:
            logging.error(f"{step_name} returned non-JSON response for {context}.")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except Exception as ex:
            logging.error(f"Unexpected error during {step_name} for {context}: {ex}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        return None

    def run(self) -> bool:
        run_started_at = datetime.now()
        run_user = ""
        step_records = []
        success_count = 0
        failure_count = 0
        all_success = True

        payload_packages = ASN_Verify_Payload_Generator().generate_payload_packages()
        if not payload_packages:
            logging.error("No valid payload packages were generated for ASN verify/check out/release flow.")
            run_ended_at = datetime.now()
            ExecutionReportWriter().write_step_report(
                step_name="ASN Verify, Check Out and Release Dock Door",
                run_user=os.getenv("USER", ""),
                started_at=run_started_at,
                ended_at=run_ended_at,
                status="FAILED",
                summary={"TotalRows": 0, "SuccessfulRows": 0, "FailedRows": 0},
                records=[{"Error": "No valid payload packages generated from MasterInput."}],
            )
            return False

        for package in payload_packages:
            environment = str(package.get("environment", "")).strip()
            plant = str(package.get("plant", "")).strip()
            context = f"{environment.upper()}/{plant}"

            verify_payload = package.get("verify_payload", [])
            check_out_payload = package.get("check_out_payload", {})
            release_dock_payload = package.get("release_dock_payload", [])
            asn_ids = package.get("asn_ids", [])
            trailer_id = str(package.get("trailer_id", "")).strip()
            location_id = str(package.get("location_id", "")).strip()

            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant)
                bearer_token = token_handler.get_bearer()
                run_user = run_user or str(getattr(token_handler, "username", "")).strip()
            except Exception as ex:
                all_success = False
                failure_count += 1
                logging.error(f"Token fetch failed for {context}: {ex}")
                step_records.append(
                    {
                        "Context": context,
                        "ASNIDs": ";".join(asn_ids),
                        "TrailerId": trailer_id,
                        "LocationId": location_id,
                        "Result": "FAILED",
                        "FailedAt": "Token",
                        "Error": str(ex),
                    }
                )
                continue

            env_handler = AWM_Env()
            env_handler.get_wm_host(host=environment.lower(), facility=plant)
            urls = {
                "verify_asn": env_handler.get_program_url("ASN_Verify"),
                "check_out": env_handler.get_program_url("Check_Out"),
                "release_dock_door": env_handler.get_program_url("Release_Dock_Door"),
            }
            if not all(urls.values()):
                all_success = False
                failure_count += 1
                logging.error(f"Endpoint resolution failed for {context}: {urls}")
                step_records.append(
                    {
                        "Context": context,
                        "ASNIDs": ";".join(asn_ids),
                        "TrailerId": trailer_id,
                        "LocationId": location_id,
                        "Result": "FAILED",
                        "FailedAt": "EndpointResolution",
                        "Error": "One or more endpoints unresolved",
                    }
                )
                continue

            headers = {
                "Content-Type": "application/json",
                "selectedOrganization": plant,
                "selectedLocation": plant,
                "Authorization": f"Bearer {bearer_token}",
            }

            verify_response = self._post_step(
                urls["verify_asn"], headers, verify_payload, "Verify ASN", context
            )
            if verify_response is None:
                all_success = False
                failure_count += 1
                step_records.append(
                    {
                        "Context": context,
                        "ASNIDs": ";".join(asn_ids),
                        "TrailerId": trailer_id,
                        "LocationId": location_id,
                        "Result": "FAILED",
                        "FailedAt": "VerifyASN",
                        "Error": "Verify ASN request failed",
                    }
                )
                continue

            release_response = self._post_step(
                urls["release_dock_door"],
                headers,
                release_dock_payload,
                "Release Dock Door",
                context,
            )
            if release_response is None:
                all_success = False
                failure_count += 1
                step_records.append(
                    {
                        "Context": context,
                        "ASNIDs": ";".join(asn_ids),
                        "TrailerId": trailer_id,
                        "LocationId": location_id,
                        "Result": "FAILED",
                        "FailedAt": "ReleaseDockDoor",
                        "Error": "Release Dock Door request failed",
                    }
                )
                continue

            check_out_result = self._post_checkout_with_fallback(
                urls["check_out"], headers, check_out_payload, context
            )
            if not check_out_result.get("success"):
                all_success = False
                failure_count += 1
                step_records.append(
                    {
                        "Context": context,
                        "ASNIDs": ";".join(asn_ids),
                        "TrailerId": trailer_id,
                        "LocationId": location_id,
                        "Result": "FAILED",
                        "FailedAt": "CheckOut",
                        "Error": "Check Out request failed",
                    }
                )
                continue
            check_out_response = check_out_result.get("response") or {}

            success_count += 1
            step_records.append(
                {
                    "Context": context,
                    "ASNIDs": ";".join(asn_ids),
                    "TrailerId": trailer_id,
                    "LocationId": location_id,
                    "VerifyASN_Success": verify_response.get("success", "N/A")
                    if isinstance(verify_response, dict)
                    else "N/A",
                    "CheckOut_Success": check_out_response.get("success", "N/A")
                    if isinstance(check_out_response, dict)
                    else "N/A",
                    "ReleaseDockDoor_Success": release_response.get("success", "N/A")
                    if isinstance(release_response, dict)
                    else "N/A",
                    "Result": "SUCCESS",
                }
            )

        run_ended_at = datetime.now()
        report_path = ExecutionReportWriter().write_step_report(
            step_name="ASN Verify, Check Out and Release Dock Door",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status="SUCCESS" if all_success else ("PARTIAL" if success_count else "FAILED"),
            summary={
                "TotalRows": len(payload_packages),
                "SuccessfulRows": success_count,
                "FailedRows": failure_count,
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")
        return all_success


if __name__ == "__main__":
    ok = ASN_Verify_CheckOut_Release().run()
    sys.exit(0 if ok else 1)
