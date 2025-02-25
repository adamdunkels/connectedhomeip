#
#    Copyright (c) 2023 Project CHIP Authors
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import logging
from dataclasses import dataclass

import chip.clusters as Clusters
from chip import ChipUtility
from chip.exceptions import ChipStackError
from chip.interaction_model import InteractionModelError, Status
from matter_testing_support import MatterBaseTest, async_test_body, default_matter_test_main, type_matches
from mobly import asserts


@dataclass
class FakeInvalidBasicInformationCommand(Clusters.BasicInformation.Commands.MfgSpecificPing):
    @ChipUtility.classproperty
    def must_use_timed_invoke(cls) -> bool:
        return False


class TC_IDM_1_4(MatterBaseTest):

    @async_test_body
    async def test_TC_IDM_1_4(self):
        dev_ctrl = self.default_controller
        dut_node_id = self.dut_node_id

        self.print_step(0, "Commissioning - already done")

        self.print_step(1, "Get remote node's MaxPathsPerInvoke")
        session_parameters = dev_ctrl.GetRemoteSessionParameters(dut_node_id)
        max_paths_per_invoke = session_parameters.maxPathsPerInvoke

        asserts.assert_greater_equal(max_paths_per_invoke, 1, "Unexpected error returned from unsupported endpoint")
        asserts.assert_less_equal(max_paths_per_invoke, 65535, "Unexpected error returned from unsupported endpoint")

        self.print_step(2, "Sending `MaxPathsPerInvoke + 1` InvokeRequest if it fits into single MTU")
        # In practice, it was noticed that we could only fit 57 commands before we hit the MTU limit as a result we
        # conservatively try putting up to 100 commands into an Invoke request. We are expecting one of 2 things to
        # happen if max_paths_per_invoke + 1 is greater than what cap_for_batch_commands is set to:
        # 1. Client (TH) fails to send command, since we cannot fit all the commands single MTU.
        #    When this happens we get ChipStackError with CHIP_ERROR_NO_MEMORY. Test step is skipped
        #    as per test spec instructions
        # 2. Client (TH) able to send command. While unexpected we will hit two different test failure depending on
        #    what the server does.
        #    a. Server successfully handle command and send InvokeResponse with results of all individual commands
        #       being failure. In this case, test fails on unexpected successes like this
        #    b. Server fails to handle command that is between cap_for_batch_commands and max_paths_per_invoke + 1.
        #       In this case, test fails as device should have actually succeeded and been caught in 2.a.
        cap_for_batch_commands = 100
        number_of_commands_to_send = min(max_paths_per_invoke + 1, cap_for_batch_commands)

        invalid_command_id = 0xffff_ffff
        list_of_commands_to_send = []
        for endpoint_index in range(number_of_commands_to_send):
            # Using Toggle command to form the base as it is a command that doesn't take
            # any arguments, this allows us to fit as more requests into single MTU.
            invalid_command = Clusters.OnOff.Commands.Toggle()
            # This is how we make the command invalid
            invalid_command.command_id = invalid_command_id

            list_of_commands_to_send.append(Clusters.Command.InvokeRequestInfo(endpoint_index, invalid_command))

        asserts.assert_greater_equal(len(list_of_commands_to_send), 2,
                                     "Step 2 is always expected to try sending at least 2 command, something wrong with test logic")
        try:
            await dev_ctrl.SendBatchCommands(dut_node_id, list_of_commands_to_send)
            # If you get the assert below it is likely because cap_for_batch_commands is actually too low.
            # This might happen after TCP is enabled and DUT supports TCP.
            asserts.fail(
                f"Unexpected success return from sending too many commands, we sent {number_of_commands_to_send}, test capped at {cap_for_batch_commands}")
        except InteractionModelError as e:
            # This check is for 2.a., mentioned above introduction of variable cap_for_batch_commands.
            asserts.assert_equal(number_of_commands_to_send, max_paths_per_invoke + 1,
                                 "Test didn't send as many command as max_paths_per_invoke + 1, likely due to MTU cap_for_batch_commands, but we still got an error from server. This should have been a success from server")
            asserts.assert_equal(e.status, Status.InvalidAction,
                                 "DUT sent back an unexpected error, we were expecting InvalidAction")
            self.print_step(2, "DUT successfully failed to process `MaxPathsPerInvoke + 1` InvokeRequests")
        except ChipStackError as e:
            chip_error_no_memory = 0x0b
            asserts.assert_equal(e.err, chip_error_no_memory, "Unexpected error while trying to send InvokeRequest")
            # TODO it is possible we want to confirm DUT can handle up to MTU max. But that is not in test plan as of right now.
            # Additionally CommandSender is not currently set up to enable caller to fill up to MTU. This might be coming soon,
            # just that it is not supported today.
            self.print_step(2, "DUTs reported MaxPathsPerInvoke + 1 is larger than what fits into MTU. Test step is skipped")

        if max_paths_per_invoke == 1:
            # TODO(#31139) After issue is resolved use that API properly to mark tests steps as skipped
            self.print_step(3, "Skipping test step as max_paths_per_invoke == 1")
            self.print_step(4, "Skipping test step as max_paths_per_invoke == 1")
            self.print_step(5, "Skipping test step as max_paths_per_invoke == 1")
            self.print_step(6, "Skipping test step as max_paths_per_invoke == 1")
            self.print_step(7, "Skipping test step as max_paths_per_invoke == 1")
            self.print_step(8, "Skipping test step as max_paths_per_invoke == 1")
            self.print_step(9, "Skipping test step as max_paths_per_invoke == 1")
        else:
            await self.steps_3_to_9(False)

    async def steps_3_to_9(self, dummy_value):
        dev_ctrl = self.default_controller
        dut_node_id = self.dut_node_id

        self.print_step(3, "Sending sending two InvokeRequest with idential paths")
        command = Clusters.BasicInformation.Commands.MfgSpecificPing()
        endpoint = 0
        invoke_request_1 = Clusters.Command.InvokeRequestInfo(endpoint, command)
        try:
            result = await dev_ctrl.SendBatchCommands(dut_node_id, [invoke_request_1, invoke_request_1])
            asserts.fail("Unexpected success return after sending two identical (non-unique) paths in the InvokeRequest")
        except InteractionModelError as e:
            asserts.assert_equal(e.status, Status.InvalidAction,
                                 "DUT sent back an unexpected error, we were expecting InvalidAction")
            logging.info("DUT successfully failed to process two InvokeRequests that contains non-unique paths")

        self.print_step(4, "Skipping test until https://github.com/project-chip/connectedhomeip/issues/30986 resolved")

        self.print_step(5, "Verify DUT is able to responsed to InvokeRequestMessage that contains two valid paths")
        endpoint = 0
        command = Clusters.OperationalCredentials.Commands.CertificateChainRequest(
            Clusters.OperationalCredentials.Enums.CertificateChainTypeEnum.kDACCertificate)
        invoke_request_1 = Clusters.Command.InvokeRequestInfo(endpoint, command)

        command = Clusters.GroupKeyManagement.Commands.KeySetRead(0)
        invoke_request_2 = Clusters.Command.InvokeRequestInfo(endpoint, command)
        try:
            result = await dev_ctrl.SendBatchCommands(dut_node_id, [invoke_request_1, invoke_request_2])
            asserts.assert_true(type_matches(result, list), "Unexpected return from SendBatchCommands")
            asserts.assert_equal(len(result), 2, "Unexpected number of InvokeResponses sent back from DUT")
            asserts.assert_true(type_matches(
                result[0], Clusters.OperationalCredentials.Commands.CertificateChainResponse), "Unexpected return type for first InvokeRequest")
            asserts.assert_true(type_matches(
                result[1], Clusters.GroupKeyManagement.Commands.KeySetReadResponse), "Unexpected return type for second InvokeRequest")
            self.print_step(5, "DUT successfully responded to a InvokeRequest action with two valid commands")
        except InteractionModelError:
            asserts.fail("DUT failed to successfully responded to a InvokeRequest action with two valid commands")

        self.print_step(6, "Skipping test until https://github.com/project-chip/connectedhomeip/issues/30991 resolved")

        self.print_step(7, "Skipping test until https://github.com/project-chip/connectedhomeip/issues/30986 resolved")

        self.print_step(8, "Verify DUT is able to responsed to InvokeRequestMessage that contains two valid paths. One of which requires timed invoke, and TimedRequest in InvokeResponseMessage set to true")
        endpoint = 0
        command = Clusters.GroupKeyManagement.Commands.KeySetRead(0)
        invoke_request_1 = Clusters.Command.InvokeRequestInfo(endpoint, command)

        command = Clusters.AdministratorCommissioning.Commands.RevokeCommissioning()
        invoke_request_2 = Clusters.Command.InvokeRequestInfo(endpoint, command)
        try:
            result = await dev_ctrl.SendBatchCommands(dut_node_id, [invoke_request_1, invoke_request_2], timedRequestTimeoutMs=5000)
            asserts.assert_true(type_matches(result, list), "Unexpected return from SendBatchCommands")
            asserts.assert_equal(len(result), 2, "Unexpected number of InvokeResponses sent back from DUT")
            asserts.assert_true(type_matches(
                result[0], Clusters.GroupKeyManagement.Commands.KeySetReadResponse), "Unexpected return type for first InvokeRequest")
            asserts.assert_true(type_matches(result[1], InteractionModelError), "Unexpected return type for second InvokeRequest")

            # We sent out RevokeCommissioning without an ArmSafe intentionally, confirm that it failed for that reason.
            asserts.assert_equal(result[1].status, Status.Failure,
                                 "Timed command, RevokeCommissioning, didn't fail in manner expected by test")
            window_not_open_cluster_error = 4
            asserts.assert_equal(result[1].clusterStatus, window_not_open_cluster_error,
                                 "Timed command, RevokeCommissioning, failed with incorrect cluster code")
            self.print_step(
                8, "DUT successfully responded to a InvokeRequest action with two valid commands. One of which required timed invoke, and TimedRequest in InvokeResponseMessage was set to true")
        except InteractionModelError:
            asserts.fail("DUT failed to successfully responded to a InvokeRequest action with two valid commands")

        self.print_step(9, "Skipping test until https://github.com/project-chip/connectedhomeip/issues/30986 resolved")


if __name__ == "__main__":
    default_matter_test_main()
