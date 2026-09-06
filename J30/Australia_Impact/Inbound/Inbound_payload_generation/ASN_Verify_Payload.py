from datetime import datetime, timedelta

from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet


class ASN_Verify_Payload_Generator:
    """Build payload packages for Verify ASN -> Check Out -> Release Dock Door."""

    ACTION_URL_RELEASE_DOCK = "COM-MANH-CP-DCINVENTORY/api/dcinventory/dockDoor/releaseDockDoor"

    def __init__(self):
        self.worksheet = Worksheet()

    @staticmethod
    def _minus_30_minutes_iso() -> str:
        return (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    def generate_payload_packages(self) -> list[dict]:
        rows = self.worksheet.asn_verify_checkout_release_extract()
        payload_packages = []

        for row in rows:
            environment = str(row.get("Environment", "")).strip()
            plant = str(row.get("Plant", "")).strip()
            asn_ids = row.get("ASNIDs", [])
            trailer_id = str(row.get("TrailerId", "")).strip()
            location_id = str(row.get("LocationId", "")).strip()
            carrier_id = str(row.get("CarrierId", "AUPU")).strip() or "AUPU"
            visit_type = str(row.get("VisitType", "DROP_UNLOAD")).strip() or "DROP_UNLOAD"
            trailer_status = str(row.get("TrailerStatus", "IB UnLoaded")).strip() or "IB UnLoaded"

            verify_payload = [{"AsnId": asn_id} for asn_id in asn_ids]
            check_out_payload = {
                "TrailerId": trailer_id,
                "VisitType": visit_type,
                "TrailerStatus": trailer_status,
                "CarrierId": carrier_id,
                "CheckInTime": self._minus_30_minutes_iso(),
                "CurrentLocation": location_id,
            }
            release_dock_payload = [
                {
                    "DockDoorId": location_id,
                    "ActionUrl": self.ACTION_URL_RELEASE_DOCK,
                }
            ]

            payload_packages.append(
                {
                    "environment": environment,
                    "plant": plant,
                    "asn_ids": asn_ids,
                    "trailer_id": trailer_id,
                    "location_id": location_id,
                    "verify_payload": verify_payload,
                    "check_out_payload": check_out_payload,
                    "release_dock_payload": release_dock_payload,
                }
            )

        return payload_packages
