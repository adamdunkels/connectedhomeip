/**
 *
 *    Copyright (c) 2023 Project CHIP Authors
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */

#import "MTRCommissionableData.h"
#import "MTRDeviceAttestationCredentials.h"
#import "MatterError.h"

#ifndef MTRDataSource_h
#define MTRDataSource_h

@protocol MTRDataSource <NSObject>

/**
 * @brief Queue used when calling the client code on completion blocks from any MatterTvCastingBridge API
 */
- (dispatch_queue_t _Nonnull)clientQueue;

/**
 * @brief Provide UniqueId used to generate the RotatingDeviceId advertised during commissioning by the MTRCastingApp
 * Must be at least 16 bytes (i.e. ConfigurationManager::kMinRotatingDeviceIDUniqueIDLength)
 */
- (NSData * _Nonnull)castingAppDidReceiveRequestForRotatingDeviceIdUniqueId:(id _Nonnull)sender;

/**
 * @brief Provides MTRCommissionableData (such as setupPasscode, discriminator, etc) used to get the MTRCastingApp commissioned
 */
- (MTRCommissionableData * _Nonnull)castingAppDidReceiveRequestForCommissionableData:(id _Nonnull)sender;

/**
 * @brief Provides MTRDeviceAttestationCredentials of the MTRCastingApp used during commissioning
 */
- (MTRDeviceAttestationCredentials * _Nonnull)castingAppDidReceiveRequestForDeviceAttestationCredentials:(id _Nonnull)sender;

/**
 * @brief Request to signs a message using the device attestation private key
 *
 * @param csrData - The message to sign using the attestation private key.
 * @param outRawSignature [in, out] - Buffer to receive the signature in raw <r,s> format.
 * @returns MATTER_NO_ERROR on success. Otherwise, a MATTER_ERROR with a code corresponding to the underlying failure
 */
- (MatterError * _Nonnull)castingApp:(id _Nonnull)sender didReceiveRequestToSignCertificateRequest:(NSData * _Nonnull)csrData outRawSignature:(NSData * _Nonnull * _Nonnull)outRawSignature;

@end

#endif /* MTRDataSource_h */
