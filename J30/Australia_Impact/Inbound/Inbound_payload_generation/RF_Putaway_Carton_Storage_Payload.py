import copy
import datetime
import uuid


class RF_Putaway_Carton_Storage_Payload_Generator:
    """Payload builder for RF putaway to carton storage flow."""

    def __init__(self):
        self._pallet_scan_template = self._build_pallet_scan_template()

    @staticmethod
    def _now_str() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    @staticmethod
    def _build_pallet_scan_template() -> dict:
        return {
            "workflowVO": {
                "header": {
                    "state": {
                        "@class": "com.manh.cp.dmmobilefacade.putaway.dto.PutawayVO",
                        "errorVOList": [],
                        "attributeValidationErrors": [],
                        "warningOverrideList": [],
                        "supervisorOverrideList": [],
                        "lookupRequired": False,
                        "workflowInitTime": "2026-08-06T19:24:21.192",
                        "additionalFields": {},
                        "taskingMode": False,
                        "transactionId": "NikeSystemDirectedCartonPutaway",
                        "transactionTypeId": "Putaway",
                        "configIds": {
                            "PutawayExecutionStrategy": "NikeSystemDirCartonPutawayExecutionStrategy",
                            "PutawayExecutionCriteria": "NikeSystemDirCartonPutawayExecutionCriteria",
                        },
                        "savedBarcodes": [],
                        "bufferedScanDepth": 0,
                        "bufferedScanOnError": "RESET_ON_ERROR",
                        "bufferedScanAllowDuplicateScan": False,
                        "compositeRegexes": ["^@"],
                        "showCompleteAction": True,
                        "imageCaptureEnabled": False,
                        "enableOfflineVerification": False,
                        "interimEventEnabled": False,
                        "conditionLogs": [],
                        "evaluationCache": [],
                        "inventoryAttributeExecutionDTO": {
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
                            "UniqueAttributeCaptureUOM": {
                                "uomConversionFactor": 1,
                                "standardQuantityUomId": "UNIT",
                            },
                            "NonUniqueAttributeCaptureUOM": {
                                "uomConversionFactor": 1,
                                "standardQuantityUomId": "UNIT",
                            },
                            "RemainderQtyCaptureUOM": {
                                "uomConversionFactor": 1,
                                "standardQuantityUomId": "UNIT",
                            },
                            "DefaultCaptureUOM": {},
                            "HasUniqueAttributes": False,
                            "NumberOfScansInDisplayUOM": 0,
                            "NumberOfScansInRemainderUOM": 0,
                            "EvaluateDefaultUOM": False,
                            "ExistingSecondaryValuesForCurrentUnitAttributeIdByName": {},
                            "MultiCaptureFlow": False,
                        },
                        "multiStepLocationVerificationCompleted": False,
                        "locationComponent": {},
                        "serialNumberMismatch": False,
                        "validatedInventoryAttributesForPreviousItems": {},
                        "workflowParameters": {
                            "@class": "com.manh.cp.dmmobilefacade.putaway.configuration.PutawayCriteria",
                            "extensionFields": {},
                            "criteriaExtensionFields": {},
                            "overrideCriteriaExtensionFields": {},
                            "itemOverrideCriteriaExtensionFields": {},
                            "laborActivityId": "System Directed ilpn Putaway",
                            "facilityProcessingMode": "DEFAULT",
                            "excludedActions": [
                                "ViewItemAttributes",
                                "GenerateDestinationIlpnForSystemDirected",
                                "GenerateIlpn",
                                "SubstituteLocation",
                                "SubstituteLocationForPutCart",
                                "NextDropZone",
                            ],
                            "conditionLoggingEnabled": False,
                            "putawayExecutionModeId": "SYSTEM_DIRECTED",
                            "putawayExecutionCriteriaId": "NikeSystemDirCartonPutawayExecutionCriteria",
                            "containerScanModeId": "ILPN_OR_Pallet",
                            "assignTaskToCurrentUser": True,
                            "itemVerificationRequired": False,
                            "displayItemAndQuantity": False,
                            "allowSplitting": False,
                            "promptForReasonCode": False,
                            "defaultReasonCodeId": "RC1",
                            "displayNeedQuantity": False,
                            "scanLocationPerContainer": False,
                            "locationVerificationModeId": "SCAN_LOCATION_BARCODE",
                            "skipDestinationLocationScanForConsolidation": False,
                            "autoGenerateIlpn": False,
                            "multiIlpnContinuousTravel": False,
                            "displayConciseVicinityDefinition": False,
                            "disableItemDateVerification": False,
                        },
                        "fromLocationVO": {"translated": True, "nextLocation": False},
                        "locationVO": {"translated": True, "nextLocation": False},
                        "itemBatchTracking": False,
                        "scannedQuantityAsUnits": 0,
                        "expectedContainerList": [],
                        "exceptionFlow": False,
                        "taskDTOList": [],
                        "initiatedByAnotherTransaction": False,
                        "overrideAssignTaskToCurrentUserFlag": False,
                        "splitFlow": False,
                        "dropZone": False,
                        "residualPutaway": False,
                        "transitionToUserDirected": False,
                        "allocationsCreatedByCurrentUser": False,
                        "verifyLpn": False,
                        "allLPNsAllocatedToSameLocation": False,
                        "palletHasResidualInventory": False,
                        "switchToUserDirectedPutaway": False,
                        "lpnConsolidation": False,
                        "nextMoveToSameLocation": False,
                        "taskDetailsChainedForExecution": [],
                        "containersFailedExecution": [],
                        "containersPlannedByCurrentUser": [],
                        "putawayInvocationFailedOnChaining": False,
                        "ignoreTaskCreationTemplate": False,
                        "skipContainerValidationForUserDirectedFlow": False,
                        "skipContainerScan": False,
                        "skipDetail": False,
                        "initiatedByLpnDisposition": False,
                        "initiatedByPickPack": False,
                        "multiItemContainer": False,
                        "acceptDestinationIlpn": False,
                        "activeLocation": False,
                        "lpnTrackedActiveLocation": False,
                        "lpnTrackedReserveLocation": False,
                        "lessThanSystemQuantityScanned": False,
                        "splitAndAllocateMultiItemContainer": False,
                        "nextItemInventoryExistsInMultiItemLpn": False,
                        "loopOnQuantity": False,
                        "toggleVO": [],
                        "renderItemAttributesScreen": False,
                        "displayItemAttributesList": [],
                        "itemInventorySpecificationMap": {},
                        "initiateTaskExecutionInNewFlow": False,
                        "multiItemTask": False,
                        "currentMoveCompletedPostDestinationIlpnScan": False,
                        "verifyItemAndQuantityForSingleItemMultiDetailMove": False,
                        "handleMultiContainerForChaining": False,
                        "cancelledTaskDetailIdsForLocate": [],
                        "alternateTaskDetailIdToOriginalPutLocationIdMap": {},
                        "sendLaborUpdateForNextDropZone": True,
                        "generateChainingEnabledLaborMessage": False,
                        "ignoreSourceLocationForTravel": False,
                        "displayItemScanQuantityForSingleItemSingleLineIlpn": False,
                        "repromptItemScanScreen": False,
                        "supportItemIdAndBarcodeScan": False,
                        "suggestedArea": "",
                        "suggestedZone": "",
                        "suggestedAisle": "",
                        "suggestedBay": "",
                        "nextMovePresent": False,
                        "putawayVicinityDefinitionId": "",
                        "multiStepLocationComponentLabel": "",
                        "previousMultiStepLocationComponentLabel": "",
                        "multiStepComponentValueFromMap": "",
                        "networkTraceEnabled": False,
                        "NavigateToRestartPutawayAfterUserDirectedLocationScan": False,
                        "scannedContainerBarcode": "",
                    },
                    "workflowScriptName": "Putaway",
                    "currentState": "AcceptContainerForSystemDirectedPutaway",
                    "breadCrumbs": {
                        "stateNames": ["AcceptContainerForSystemDirectedPutaway"],
                        "activeItems": {"AcceptContainerForSystemDirectedPutaway": "label.ContainerId"},
                        "internalStates": ["EntryScreenForPutaway"],
                        "parsedBarcodes": {},
                        "scannedBarcodeLists": {},
                        "consumedBarcodeValues": [],
                    },
                    "status": "SUCCESS",
                    "exitInvoked": False,
                    "flowChainCompleted": False,
                    "screenTitle": "NikeSystemDirectedCartonPutaway",
                    "allowExit": True,
                    "workflowActionList": [],
                    "autoProcessNext": False,
                    "globalState": {},
                    "returnToNormalFlowOnly": False,
                    "labelForm": "Standard",
                    "userName": "",
                    "custom": False,
                },
                "userInputs": [],
                "links": [],
                "userDisplays": [],
                "idempotencyKey": str(uuid.uuid4()),
            }
        }

    @staticmethod
    def _state_from_payload(payload: dict) -> dict:
        return payload.setdefault("workflowVO", {}).setdefault("header", {}).setdefault("state", {})

    @staticmethod
    def _header_from_payload(payload: dict) -> dict:
        return payload.setdefault("workflowVO", {}).setdefault("header", {})

    def _refresh_runtime_fields(self, node, run_user: str):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                normalized = str(key).strip().lower()
                if normalized == "idempotencykey":
                    node[key] = str(uuid.uuid4())
                    continue
                if normalized in {
                    "workflowinittime",
                    "taskstarttime",
                    "createdtimestamp",
                    "updatedtimestamp",
                    "checkintime",
                }:
                    node[key] = self._now_str()
                    continue
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

    def _set_runtime_user(self, payload: dict, run_user: str):
        if run_user:
            header = self._header_from_payload(payload)
            header["userName"] = run_user

    @staticmethod
    def _clone_response_as_payload(previous_response: dict) -> dict:
        if not isinstance(previous_response, dict):
            return {}
        payload = copy.deepcopy(previous_response)
        if "workflowVO" not in payload and "data" in payload and isinstance(payload["data"], dict):
            data = payload["data"]
            if "workflowVO" in data:
                payload = copy.deepcopy(data)
        return payload

    def build_pallet_scan_payload(self, pallet_id: str, run_user: str = "") -> dict:
        payload = copy.deepcopy(self._pallet_scan_template)
        state = self._state_from_payload(payload)
        state["scannedContainerBarcode"] = pallet_id
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_scan_location_payload(self, previous_response: dict, run_user: str = "") -> dict:
        payload = self._clone_response_as_payload(previous_response)
        state = self._state_from_payload(payload)
        location_barcode = str(state.get("locationVO", {}).get("barcode", "")).strip()
        if location_barcode:
            state["scannedLocationBarcode"] = location_barcode
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_carton_scan_payload(self, previous_response: dict, run_user: str = "") -> dict:
        payload = self._clone_response_as_payload(previous_response)
        state = self._state_from_payload(payload)
        expected_container_id = str(state.get("containerId", "")).strip()
        if expected_container_id:
            state["scannedContainerBarcode"] = expected_container_id
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload
