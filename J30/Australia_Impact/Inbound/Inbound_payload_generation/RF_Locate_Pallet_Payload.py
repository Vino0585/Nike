import copy
import datetime
import uuid


class RF_Locate_Pallet_Payload_Generator:
    """Payload builder for RF pallet locate flows (staging then drop location)."""

    def __init__(self):
        self._scan_template = self._build_scan_pallet_template()

    @staticmethod
    def _now_str() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    @staticmethod
    def _build_scan_pallet_template() -> dict:
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
                        "workflowInitTime": "2026-09-02T12:45:15.985",
                        "additionalFields": {},
                        "taskingMode": False,
                        "transactionId": "NikeLocateiLPN",
                        "transactionTypeId": "Putaway",
                        "configIds": {
                            "PutawayExecutionStrategy": "NikeLocateCartonNPallet",
                            "PutawayExecutionCriteria": "NikeLocateExecutionCriteria",
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
                            "laborActivityId": "User Directed ilpn Putaway",
                            "facilityProcessingMode": "DEFAULT",
                            "excludedActions": ["NextDropZone"],
                            "conditionLoggingEnabled": False,
                            "putawayExecutionModeId": "USER_DIRECTED",
                            "putawayExecutionCriteriaId": "NikeLocateExecutionCriteria",
                            "containerScanModeId": "ILPN_OR_Pallet",
                            "assignTaskToCurrentUser": False,
                            "itemVerificationRequired": False,
                            "itemVerificationModeId": "DISPLAY_ITEM_SCAN_QTY",
                            "displayItemAndQuantity": False,
                            "allowSplitting": False,
                            "promptForReasonCode": False,
                            "displayNeedQuantity": False,
                            "scanLocationPerContainer": False,
                            "locationVerificationModeId": "SCAN_LOCATION_BARCODE",
                            "skipDestinationLocationScanForConsolidation": False,
                            "autoGenerateIlpn": False,
                            "multiIlpnContinuousTravel": False,
                            "displayConciseVicinityDefinition": True,
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
                        "containersForUserDirectedPutaway": [],
                        "putawayInvocationFailedOnChaining": False,
                        "ignoreTaskCreationTemplate": False,
                        "skipContainerValidationForUserDirectedFlow": False,
                        "skipContainerScan": False,
                        "skipDetail": False,
                        "initiatedByLpnDisposition": False,
                        "userDirectedPutawayInitiatedByLpnDisposition": False,
                        "userDirectedPutawayAllFromDisposition": False,
                        "initiatedByPickPack": False,
                        "containersForUserDirectedPutawayDisplayList": [],
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
                    "currentState": "AcceptContainerForUserDirectedPutaway",
                    "breadCrumbs": {
                        "stateNames": ["AcceptContainerForUserDirectedPutaway"],
                        "activeItems": {
                            "AcceptContainerForUserDirectedPutaway": "label.ContainerId"
                        },
                        "internalStates": ["EntryScreenForPutaway"],
                        "parsedBarcodes": {},
                        "scannedBarcodeLists": {},
                        "consumedBarcodeValues": [],
                    },
                    "status": "SUCCESS",
                    "exitInvoked": False,
                    "flowChainCompleted": False,
                    "screenTitle": "NikeLocateiLPN",
                    "allowExit": True,
                    "workflowActionList": [],
                    "autoProcessNext": False,
                    "globalState": {},
                    "returnToNormalFlowOnly": False,
                    "labelForm": "Standard",
                    "userName": "",
                    "custom": False,
                },
                "userInputs": [
                    {
                        "action": "AcceptContainerForUserDirectedPutaway",
                        "inputType": "barcodeTextField",
                        "inputLabel": "Scan Container",
                        "originalLabel": "input.ContainerId",
                        "helpInfo": "scannedContainerBarcode",
                        "inputObject": "scannedContainerBarcode",
                        "required": True,
                        "errors": [],
                        "barcodeTypes": ["ILPN", "IBPallet"],
                        "validateBarcode": True,
                        "barcodeLastNs": [3, 3],
                        "maxScans": 1,
                        "voiceDisplay": "Scan Container",
                        "speechText": "Scan Container",
                        "allowNegative": False,
                        "additionalField": False,
                    }
                ],
                "links": [],
                "userDisplays": [],
                "idempotencyKey": str(uuid.uuid4()),
            }
        }

    def _refresh_runtime_fields(self, node, run_user: str):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                normalized = str(key).strip().lower()
                if normalized in {"idempotencykey"}:
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
        if not run_user:
            return
        header = payload.setdefault("workflowVO", {}).setdefault("header", {})
        header["userName"] = run_user

    def _clone_response_as_payload(self, previous_response: dict) -> dict:
        if not isinstance(previous_response, dict):
            return {}
        payload = copy.deepcopy(previous_response)
        if "workflowVO" not in payload and "data" in payload and isinstance(payload["data"], dict):
            inner = payload["data"]
            if "workflowVO" in inner:
                payload = copy.deepcopy(inner)
        return payload

    def build_staging_scan_pallet_payload(self, pallet_id: str, run_user: str = "") -> dict:
        payload = copy.deepcopy(self._scan_template)
        state = payload["workflowVO"]["header"]["state"]
        state["scannedContainerBarcode"] = pallet_id
        state["containerId"] = pallet_id
        state["containerType"] = "PALLET"
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_staging_accept_location_payload(
        self,
        previous_response: dict,
        location_barcode: str,
        run_user: str = "",
    ) -> dict:
        payload = self._clone_response_as_payload(previous_response)
        state = payload.setdefault("workflowVO", {}).setdefault("header", {}).setdefault("state", {})
        state["scannedLocationBarcode"] = location_barcode
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_staging_confirm_put_payload(self, previous_response: dict, run_user: str = "") -> dict:
        payload = self._clone_response_as_payload(previous_response)
        state = payload.setdefault("workflowVO", {}).setdefault("header", {}).setdefault("state", {})
        state["warningOverrideList"] = ["PTW::135"]
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload

    def build_drop_scan_pallet_payload(self, pallet_id: str, run_user: str = "") -> dict:
        return self.build_staging_scan_pallet_payload(pallet_id=pallet_id, run_user=run_user)

    def build_drop_accept_location_payload(
        self,
        previous_response: dict,
        location_barcode: str,
        run_user: str = "",
    ) -> dict:
        payload = self._clone_response_as_payload(previous_response)
        state = payload.setdefault("workflowVO", {}).setdefault("header", {}).setdefault("state", {})
        state["scannedLocationBarcode"] = location_barcode
        self._set_runtime_user(payload, run_user)
        self._refresh_runtime_fields(payload, run_user)
        return payload
