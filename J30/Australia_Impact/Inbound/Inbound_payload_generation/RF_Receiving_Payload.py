import copy
import datetime
import json
import logging
import sys
import uuid
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Inbound.Inbound_payload_generation.Inbound_State_Manager import StateManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RF_Receiving_Payload_Generator:
    def __init__(self):
        self.state_manager = StateManager()
        templates = self._load_local_templates()
        self.dock_template = templates.get("dock", self._build_default_dock_template())
        self.shipment_template = templates.get("shipment", self._build_default_shipment_template())
        self.lpn_template = templates.get("lpn", self._build_default_lpn_template())
        self.pallet_template = templates.get("pallet", self._build_default_pallet_template())

    @staticmethod
    def _template_file_path() -> Path:
        return Path(__file__).resolve().parent / "rf_payload_templates.json"

    def _load_local_templates(self) -> dict:
        template_path = self._template_file_path()
        if not template_path.exists():
            logging.warning(f"RF payload template file not found at {template_path}; using built-in templates.")
            return {}
        try:
            templates = json.loads(template_path.read_text(encoding="utf-8"))
            if isinstance(templates, dict):
                return templates
        except Exception as ex:
            logging.error(f"Failed to read RF payload templates from {template_path}: {ex}")
        logging.warning("Using built-in RF templates due to template-file parse issue.")
        return {}

    @staticmethod
    def _now_str() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    def _build_default_dock_template(self) -> dict:
        now = self._now_str()
        return {
            "workflowVO": {
                "header": {
                    "state": {
                        "@class": "com.manh.cp.dmmobilefacade.receiving.dto.ReceivingDTO",
                        "errorVOList": [],
                        "attributeValidationErrors": [],
                        "warningOverrideList": [],
                        "supervisorOverrideList": [],
                        "lookupRequired": False,
                        "workflowInitTime": now,
                        "additionalFields": {},
                        "taskingMode": False,
                        "taskStartTime": now,
                        "transactionId": "Recv and Sort",
                        "transactionTypeId": "Receive",
                        "configIds": {
                            "ReceivingCriteria": "NikeRegularRecvLPNLevelCriteria",
                            "ReceivingStrategy": "NikeRegularReceivingStrategy",
                        },
                        "savedBarcodes": [],
                        "bufferedScanDepth": 0,
                        "bufferedScanOnError": "RESET_ON_ERROR",
                        "bufferedScanAllowDuplicateScan": False,
                        "compositeRegexes": [],
                        "showCompleteAction": True,
                        "imageCaptureEnabled": False,
                        "enableOfflineVerification": False,
                        "interimEventEnabled": False,
                        "conditionLogs": [],
                        "evaluationCache": [],
                        "workflowParameters": {
                            "@class": "com.manh.cp.dmmobilefacade.receiving.configuration.ReceivingExecutionCriteria",
                            "extensionFields": {
                                "EX02ModEnabled": False,
                                "EX01ReturnRcv": False,
                                "EnableRsoHoldCheck": False,
                            },
                            "criteriaExtensionFields": {
                                "EX02ModEnabled": False,
                                "EX01ReturnRcv": False,
                                "EnableRsoHoldCheck": False,
                            },
                            "overrideCriteriaExtensionFields": {},
                            "itemOverrideCriteriaExtensionFields": {},
                            "laborActivityId": "Default Receiving Activity",
                            "instructionSets": {},
                            "facilityProcessingMode": "DEFAULT",
                            "excludedActions": ["VerifyShipment", "VerifyASN", "ReleaseDoor", "ASNReceived"],
                            "conditionLoggingEnabled": False,
                            "receivingMode": "LPN",
                            "dispositionTransactionId": "LPN Disposition",
                            "displayUomId": "UNIT",
                            "promptForLpn": True,
                            "receivingCriteriaId": "NikeRegularRecvLPNLevelCriteria",
                            "promptForPallet": "DO_NOT_PROMPT_FOR_PALLET",
                            "quantityMode": "KEY_QUANTITY",
                            "receiveWithoutAsn": True,
                            "promptForPalletId": "DO_NOT_PROMPT_FOR_PALLET",
                            "promptAsnShipmentAttribute": False,
                            "verifyItem": False,
                            "promptForAsn": False,
                            "promptForShipment": True,
                            "captureNonUniqueAttributeForAsnLine": False,
                            "displayShippedQuantityForLpnLevelAsn": False,
                            "promptInventoryAttributesId": "PROMPT_IF_NULL",
                            "promptForDockDoor": True,
                            "promptPOAndVendorForBlindItem": False,
                            "promptTrailerStatus": False,
                            "locateLpnToStaging": "STAGE_LOCATION_FROM_DOCK_DOOR",
                        },
                        "EnableBlindReceipt": True,
                        "PromptForPallet": "DO_NOT_PROMPT_FOR_PALLET",
                        "ReceivingMode": "LPN",
                        "ReceivingStrategyId": "NikeRegularReceivingStrategy",
                        "AllowASNVerification": "ALLOW_ASN_VERIFICATION_WITH_VARIANCE",
                        "AnyLeftInTrailerMessage": "Anything left in the trailer to be Received?",
                        "AnyLeftInTrailer": False,
                        "PreReceiptMode": False,
                        "PromptForPO": False,
                        "PromptForASN": False,
                        "PromptForDockDoorASN": False,
                        "RenderItemAttributesScreen": False,
                        "NullInventoryAttributesExist": False,
                        "PromptBatchExpirationDate": False,
                        "RenderLpnDetailDatesScreen": False,
                        "dockDoorLocationBarCode": "",
                        "DockDoorId": "",
                        "DockDoorShipmentIdList": [],
                        "DisplayShipmentList": False,
                        "DisplayTotalShippedAndReceivedQuantity": False,
                        "EnableAssociateAdditionalAsn": False,
                        "ItemVerificationRequired": False,
                        "PromptDisplayItemLocationCapacity": False,
                        "AdditionalLpnIds": [],
                        "PromptPackQuantity": False,
                        "InvokePackQuantityValidations": False,
                        "IsCopyLpnFlow": False,
                        "IsBlindItem": False,
                        "QuantityInUnitsFromUserInput": 0,
                        "StashedWarningOverrides": [],
                        "AsnIdsAssignedToDockDoor": [],
                        "LPNDetailIndex": 0,
                        "LPNExists": False,
                        "ASNExists": False,
                        "LPNPreAllocated": False,
                    },
                    "workflowScriptName": "Receiving",
                    "currentState": "AcceptDockDoor",
                    "breadCrumbs": {
                        "stateNames": ["AcceptDockDoor"],
                        "activeItems": {"AcceptDockDoor": "label.DockDoorId"},
                        "internalStates": ["EntryScreenForReceiving"],
                        "parsedBarcodes": {},
                        "scannedBarcodeLists": {},
                        "consumedBarcodeValues": [],
                    },
                    "status": "SUCCESS",
                    "exitInvoked": False,
                    "flowChainCompleted": False,
                    "screenTitle": "Recv and Sort",
                    "allowExit": True,
                    "workflowActionList": [
                        "InterimEvent",
                        "EmployeePerformance",
                        "AssetCapture",
                        "VerifyASN",
                        "VerifyShipment",
                        "ASNReceived",
                        "AssociateAdditionalShipment",
                        "ReleaseDoor",
                        "AssociateAdditionalAsn",
                        "AsnScanMode",
                        "RrnScanMode",
                        "CustomerOrderScanMode",
                        "VendorPerformance",
                        "EndPallet",
                        "PalletizeLPN",
                        "CopyLpn",
                        "SkipItem",
                        "AddItem",
                        "EndLPN",
                        "GenerateBatchNumber",
                        "ContinueToNextScreen",
                        "UndoLastPrimaryUniqueAttributeScan",
                        "EndPrimaryUniqueAttributeScan",
                        "UndoLastSecondaryAttributeScan",
                        "EndSecondaryInventoryAttributeMultiCaptureScan",
                        "PreAllocationSummary",
                        "EndAdditionalLPNScan",
                    ],
                    "autoProcessNext": False,
                    "globalState": {},
                    "returnToNormalFlowOnly": False,
                    "labelForm": "Standard",
                }
            },
            "userInputs": [
                {
                    "action": "AcceptDockDoor",
                    "inputType": "barcodeTextField",
                    "inputLabel": "Scan Dock Door",
                    "originalLabel": "input.DockDoorId",
                    "helpInfo": "dockDoorLocationBarCode",
                    "inputObject": "dockDoorLocationBarCode",
                    "required": False,
                    "errors": [],
                    "barcodeTypes": ["DockDoor"],
                    "validateBarcode": True,
                    "barcodeLastNs": [],
                    "maxScans": 1,
                    "voiceDisplay": "Scan Dock Door",
                    "speechText": "Scan Dock Door",
                    "allowNegative": False,
                    "additionalField": False,
                }
            ],
            "links": [
                {
                    "actionName": "AcceptDockDoor",
                    "type": "OnComplete",
                    "label": "AcceptDockDoor",
                    "voiceDisplay": "AcceptDockDoor",
                    "speechText": "AcceptDockDoor",
                    "disabled": False,
                }
            ],
            "userDisplays": [
                {
                    "type": "pair",
                    "label": "Dock Door",
                    "originalLabel": "label.DockDoorId",
                    "voiceDisplay": "Dock Door",
                    "speechText": "Dock Door",
                    "value": "dockDoorLocationBarCode",
                    "active": True,
                    "checked": False,
                    "additionalField": False,
                }
            ],
            "idempotencyKey": str(uuid.uuid4()),
        }

    def _build_default_shipment_template(self) -> dict:
        payload = copy.deepcopy(self._build_default_dock_template())
        workflow = payload["workflowVO"]
        header = workflow["header"]
        header["currentState"] = "AcceptShipment"
        header["breadCrumbs"]["stateNames"] = ["AcceptShipment", "AcceptDockDoor"]
        header["breadCrumbs"]["activeItems"]["AcceptShipment"] = "label.InboundDelivery"
        header["breadCrumbs"]["internalStates"] = ["NextStateAfterDockDoor"]
        header["submittedActionName"] = "AcceptDockDoor"
        state = header["state"]
        state["shipmentId"] = ""
        state["DockDoorShipmentIdList"] = []
        state["dataCarrier"] = {
            "translated": True,
            "title": "Shipments",
            "columns": [{"translated": True, "text": "SHIPMENT", "dataIndex": "value", "header": False}],
            "data": [],
            "type": "plainList",
            "disableClick": False,
            "enableScroll": False,
            "pageNumber": 0,
        }
        workflow["userInputs"] = [
            {
                "action": "AcceptShipment",
                "inputType": "barcodeTextField",
                "inputLabel": "Scan Inbound Delivery",
                "originalLabel": "input.InboundDelivery",
                "helpInfo": "shipmentId",
                "inputObject": "shipmentId",
                "required": False,
                "errors": [],
                "barcodeTypes": ["Shipment"],
                "validateBarcode": True,
                "barcodeLastNs": [],
                "maxScans": 1,
                "voiceDisplay": "Scan Inbound Delivery",
                "speechText": "Scan Inbound Delivery",
                "allowNegative": False,
                "additionalField": False,
            }
        ]
        workflow["links"] = [
            {
                "actionName": "AcceptShipment",
                "type": "OnComplete",
                "label": "AcceptShipment",
                "voiceDisplay": "AcceptShipment",
                "speechText": "AcceptShipment",
                "disabled": False,
            }
        ]
        workflow["userDisplays"] = [
            {
                "type": "pair",
                "label": "Inbound Delivery",
                "originalLabel": "label.InboundDelivery",
                "voiceDisplay": "Inbound Delivery",
                "speechText": "Inbound Delivery",
                "value": "shipmentId",
                "active": True,
                "checked": False,
                "additionalField": False,
            }
        ]
        return payload

    def _build_default_lpn_template(self) -> dict:
        payload = copy.deepcopy(self._build_default_shipment_template())
        workflow = payload["workflowVO"]
        header = workflow["header"]
        header["currentState"] = "AcceptLPN"
        header["breadCrumbs"]["stateNames"] = ["AcceptLPN", "AcceptShipment", "AcceptDockDoor"]
        header["breadCrumbs"]["activeItems"]["AcceptLPN"] = "label.LpnId"
        header["breadCrumbs"]["internalStates"] = [
            "NextStateAfterShipment",
            "DetermineReceivingOverrideFlow",
            "NextStateAfterDetermineReceivingOverrideFlow",
            "NextStateAfterPO",
            "NextStateAfterVendor",
            "NextStateAfterStagingLocation",
        ]
        header["submittedActionName"] = "AcceptShipment"
        state = header["state"]
        state["LPNId"] = ""
        workflow["userInputs"] = [
            {
                "action": "AcceptLPN",
                "inputType": "barcodeTextField",
                "inputLabel": "Scan LPN",
                "originalLabel": "input.LpnId",
                "helpInfo": "LPNId",
                "inputObject": "LPNId",
                "required": False,
                "errors": [],
                "barcodeTypes": ["ILPN"],
                "validateBarcode": True,
                "barcodeLastNs": [3],
                "maxScans": 1,
                "voiceDisplay": "Enter iLPN",
                "speechText": "Enter iLPN",
                "allowNegative": False,
                "additionalField": False,
            }
        ]
        workflow["links"] = [
            {
                "actionName": "AcceptLPN",
                "type": "OnComplete",
                "label": "AcceptLPN",
                "voiceDisplay": "AcceptLPN",
                "speechText": "AcceptLPN",
                "disabled": False,
            }
        ]
        workflow["userDisplays"] = [
            {
                "type": "pair",
                "label": "Dock Door",
                "originalLabel": "label.DockDoorId",
                "voiceDisplay": "Dock Door",
                "speechText": "Dock Door",
                "value": "dockDoorLocationBarCode",
                "active": False,
                "checked": True,
                "additionalField": False,
            },
            {
                "type": "pair",
                "label": "Inbound Delivery",
                "originalLabel": "label.InboundDelivery",
                "voiceDisplay": "Inbound Delivery",
                "speechText": "Inbound Delivery",
                "value": "shipmentId",
                "active": False,
                "checked": True,
                "additionalField": False,
            },
            {
                "type": "pair",
                "label": "LPN",
                "originalLabel": "label.LpnId",
                "voiceDisplay": "LPN",
                "speechText": "LPN",
                "value": "LPNId",
                "active": True,
                "checked": False,
                "additionalField": False,
            },
        ]
        return payload

    def _build_default_pallet_template(self) -> dict:
        now = self._now_str()
        return {
            "workflowVO": {
                "header": {
                    "state": {
                        "@class": "com.manh.cp.dmmobilefacade.sorting.dto.SortingDTO",
                        "errorVOList": [],
                        "attributeValidationErrors": [],
                        "warningOverrideList": [],
                        "supervisorOverrideList": [],
                        "lookupRequired": False,
                        "workflowInitTime": now,
                        "additionalFields": {},
                        "taskingMode": False,
                        "taskId": "",
                        "transactionId": "Recv and Sort",
                        "transactionTypeId": "Sort",
                        "configIds": {"SortStrategy": "Recv and Sort"},
                        "sortingMode": "SORT_TO_PALLET",
                        "defaultSortZone": "IB8008",
                        "locationVerificationMode": "SCAN_LOCATION_BARCODE",
                        "performItemSorting": False,
                        "sortCriteriaId": "Receive and Sort IB8008",
                        "sortByTaskDetail": False,
                        "quantityModeId": "KEY_QUANTITY",
                        "sortZoneId": "IB8008",
                        "containerId": "",
                        "destinationLpnId": "",
                        "palletId": "",
                        "networkTraceEnabled": False,
                    },
                    "workflowScriptName": "Sorting",
                    "currentState": "AcceptToPallet",
                    "breadCrumbs": {
                        "stateNames": ["AcceptToPallet"],
                        "activeItems": {"AcceptToPallet": "label.DirectToPalletId"},
                        "internalStates": ["EntryScreenForSorting", "AcceptLpn", "DetermineSortZone", "ProcessContainer"],
                        "parsedBarcodes": {},
                        "scannedBarcodeLists": {},
                        "consumedBarcodeValues": [],
                    },
                    "status": "SUCCESS",
                    "exitInvoked": False,
                    "flowChainCompleted": False,
                    "screenTitle": "Recv and Sort",
                    "allowExit": True,
                    "workflowActionList": [
                        "InterimEvent",
                        "EmployeePerformance",
                        "GenerateLpnId",
                        "AlternateLocation",
                        "SubstituteLocation",
                        "GeneratePalletId",
                        "OverrideToUserDirected",
                        "AlternateLocationForSystemDirected",
                        "AlternateLpnForSystemDirected",
                        "SubstituteLocationForSystemDirected",
                        "EndContainer",
                    ],
                    "autoProcessNext": False,
                    "globalState": {},
                    "returnToNormalFlowOnly": False,
                    "labelForm": "Standard",
                }
            },
            "userInputs": [
                {
                    "action": "AcceptToPallet",
                    "inputType": "barcodeTextField",
                    "inputLabel": "Scan Pallet",
                    "originalLabel": "input.PalletId",
                    "helpInfo": "palletId",
                    "inputObject": "palletId",
                    "required": True,
                    "errors": [],
                    "barcodeTypes": ["IBPallet"],
                    "validateBarcode": True,
                    "barcodeLastNs": [3],
                    "maxScans": 1,
                    "voiceDisplay": "Scan Pallet",
                    "speechText": "Scan Pallet",
                    "allowNegative": False,
                    "additionalField": False,
                }
            ],
            "links": [
                {
                    "actionName": "AcceptToPallet",
                    "type": "OnComplete",
                    "label": "AcceptToPallet",
                    "voiceDisplay": "AcceptToPallet",
                    "speechText": "AcceptToPallet",
                    "disabled": False,
                }
            ],
            "userDisplays": [
                {
                    "type": "pair",
                    "label": "Direct To Pallet",
                    "originalLabel": "label.DirectToPalletId",
                    "voiceDisplay": "Direct To Pallet",
                    "speechText": "Direct To Pallet",
                    "value": "palletId",
                    "active": True,
                    "checked": False,
                    "additionalField": False,
                }
            ],
            "idempotencyKey": str(uuid.uuid4()),
        }

    @staticmethod
    def _extract_workflow_payload(obj: dict) -> dict | None:
        if not isinstance(obj, dict):
            return None
        if "workflowVO" in obj and isinstance(obj["workflowVO"], dict):
            return copy.deepcopy(obj)
        for value in obj.values():
            if isinstance(value, dict):
                candidate = RF_Receiving_Payload_Generator._extract_workflow_payload(value)
                if candidate:
                    return candidate
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        candidate = RF_Receiving_Payload_Generator._extract_workflow_payload(item)
                        if candidate:
                            return candidate
        return None

    @staticmethod
    def _extract_header_context_for_state(obj: dict, state_name: str) -> dict | None:
        if not isinstance(obj, dict):
            return None
        if (
            "state" in obj
            and "workflowScriptName" in obj
            and str(obj.get("currentState", "")).strip() == state_name
        ):
            return copy.deepcopy(obj)
        for value in obj.values():
            if isinstance(value, dict):
                candidate = RF_Receiving_Payload_Generator._extract_header_context_for_state(
                    value, state_name
                )
                if candidate:
                    return candidate
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        candidate = RF_Receiving_Payload_Generator._extract_header_context_for_state(
                            item, state_name
                        )
                        if candidate:
                            return candidate
        return None

    @staticmethod
    def _set_common_scan_state(payload: dict, action_name: str, state_field: str, value: str):
        state = payload.setdefault("workflowVO", {}).setdefault("header", {}).setdefault("state", {})
        state[state_field] = value

        parsed = (
            payload.setdefault("workflowVO", {})
            .setdefault("header", {})
            .setdefault("breadCrumbs", {})
            .setdefault("parsedBarcodes", {})
        )
        parsed[action_name] = value

    @staticmethod
    def _set_runtime_user(payload: dict, run_user: str):
        if not run_user:
            return
        workflow = payload.setdefault("workflowVO", {})
        header = workflow.setdefault("header", {})
        header["userName"] = run_user

    def _refresh_runtime_fields(self, node, run_user: str):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                normalized = str(key).strip().lower()
                if normalized == "idempotencykey":
                    node[key] = str(uuid.uuid4())
                    continue

                # Keep workflow timestamps current for each request payload.
                if normalized in {
                    "workflowinittime",
                    "taskstarttime",
                    "createdtimestamp",
                    "updatedtimestamp",
                    "checkintime",
                }:
                    node[key] = self._now_str()
                    continue

                # Replace user fields if present in payload trees.
                if run_user and normalized in {
                    "username",
                    "createdby",
                    "updatedby",
                    "preferred_username",
                    "user_name",
                }:
                    node[key] = run_user
                    continue

                self._refresh_runtime_fields(value, run_user)
        elif isinstance(node, list):
            for item in node:
                self._refresh_runtime_fields(item, run_user)

    def build_accept_dock_door_payload(self, dock_door_id: str, run_user: str = "") -> dict:
        payload = copy.deepcopy(self.dock_template)
        self._set_common_scan_state(payload, "AcceptDockDoor", "dockDoorLocationBarCode", dock_door_id)
        state = payload["workflowVO"]["header"]["state"]
        state["DockDoorId"] = ""
        state.setdefault("inventoryAttributeExecutionDTO", {
            "FinalInventoryAttributesList": [],
            "CurrentInventoryAttributesMultiCaptureFlow": [],
            "CurrentInventoryAttributes": {},
            "SecondaryInventoryAttributes": [],
            "AllPrimaryAttributeValues": [],
            "SecondaryAttributesCapturedForCurrentUnit": [],
            "NumberOfUnits": 0,
            "QuantityInUom": 0,
            "RemainderQuantityInUom": 0,
            "ItemId": "",
            "UniqueAttributeCaptureUOM": {"uomConversionFactor": 1, "standardQuantityUomId": "UNIT"},
            "NonUniqueAttributeCaptureUOM": {"uomConversionFactor": 1, "standardQuantityUomId": "UNIT"},
            "RemainderQtyCaptureUOM": {"uomConversionFactor": 1, "standardQuantityUomId": "UNIT"},
            "DefaultCaptureUOM": {},
            "HasUniqueAttributes": False,
            "NumberOfScansInDisplayUOM": 0,
            "NumberOfScansInRemainderUOM": 0,
            "EvaluateDefaultUOM": False,
            "ExistingSecondaryValuesForCurrentUnitAttributeIdByName": {},
            "MultiCaptureFlow": False,
        })
        state.setdefault("multiStepLocationVerificationCompleted", False)
        state.setdefault("locationComponent", {})
        state.setdefault("serialNumberMismatch", False)
        state.setdefault("validatedInventoryAttributesForPreviousItems", {})
        state.setdefault("compositeItemDTOList", [])
        state.setdefault("supportItemIdScan", False)
        state.setdefault("toggleVO", [])
        state.setdefault("prevLPNDetailIndex", 0)
        state.setdefault("currentUserInputDetailIndex", 0)
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_accept_shipment_payload(self, previous_response: dict, shipment_id: str, run_user: str = "") -> dict:
        payload = self._extract_workflow_payload(previous_response) or copy.deepcopy(self.shipment_template)
        self._set_common_scan_state(payload, "AcceptShipment", "shipmentId", shipment_id)
        state = payload["workflowVO"]["header"]["state"]
        state["shipmentId"] = shipment_id
        state["DockDoorShipmentIdList"] = [shipment_id]
        data_carrier = state.get("dataCarrier")
        if isinstance(data_carrier, dict):
            data_carrier["data"] = [{"value": shipment_id}]
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_accept_lpn_payload(self, previous_response: dict, lpn_id: str, run_user: str = "") -> dict:
        payload = self._extract_workflow_payload(previous_response) or copy.deepcopy(self.lpn_template)
        self._set_common_scan_state(payload, "AcceptLPN", "LPNId", lpn_id)
        state = payload["workflowVO"]["header"]["state"]
        state["LPNId"] = lpn_id
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_accept_to_pallet_payload(self, previous_response: dict, pallet_id: str, run_user: str = "") -> dict:
        payload = self._extract_workflow_payload(previous_response) or copy.deepcopy(self.pallet_template)
        state = payload.setdefault("workflowVO", {}).setdefault("header", {}).setdefault("state", {})
        state["palletId"] = pallet_id
        parsed = (
            payload.setdefault("workflowVO", {})
            .setdefault("header", {})
            .setdefault("breadCrumbs", {})
            .setdefault("parsedBarcodes", {})
        )
        parsed["AcceptToPallet"] = pallet_id
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def extract_next_accept_lpn_payload(self, accept_pallet_response: dict, run_user: str = "") -> dict | None:
        direct_payload = self._extract_workflow_payload(accept_pallet_response)
        if direct_payload:
            header = direct_payload.get("workflowVO", {}).get("header", {})
            if str(header.get("currentState", "")).strip() == "AcceptLPN":
                return direct_payload

        header_context = self._extract_header_context_for_state(accept_pallet_response, "AcceptLPN")
        if not header_context:
            return None

        payload = copy.deepcopy(self.lpn_template)
        payload["workflowVO"]["header"] = header_context
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user=run_user)
        return payload

    def next_pallet_id(self) -> str:
        prefix = datetime.datetime.now().strftime("PAL%m%d%y")
        seq = self.state_manager.increment_counter(
            counter_name="pallet_nbr",
            start=0,
            min_value=0,
            max_value=99,
            scope=prefix,
        )
        return f"{prefix}{seq:02d}"
