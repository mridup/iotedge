iotedge dev for edge-stsdk
make some experiments with azure edge modules, especially to find out if we can create a Proxy(Translation) Gateway with the Edge device and then connect non-IP devices through the gateway to the IoTHub

Issues (on 09/10/18):
1. HSM Certificates expire sometimes (Not sure why and how):
   In such cases, iotedge runtime will error out and fail. To see error:

  "journalctl –no-pager"  -> should show below output error!

  Oct 09 05:32:31 raspberrypi iotedged[24307]: 2018-10-09T14:32:31Z [ERR!] - An hsm error occurred.
  Oct 09 05:32:31 raspberrypi iotedged[24307]: 2018-10-09T14:32:31Z [ERR!] -         caused by: HSM failure
  Oct 09 05:32:31 raspberrypi iotedged[24307]: 2018-10-09T14:32:31Z [ERR!] -         caused by: HSM Init failure: 44
  Oct 09 05:32:31 raspberrypi iotedged[24307]: 2018-10-09T14:32:31Z [ERR!] (/project/hsm-sys/azure-iot-hsm-c/src/edge_pki_openssl.c:validate_certificate_expiration:655) Certificate has expired
  Oct 09 05:32:31 raspberrypi iotedged[24307]: 2018-10-09T14:32:31Z [ERR!] (/project/hsm-sys/azure-iot-hsm-c/src/edge_pki_openssl.c:check_certificates:1366) Certificate file has expired /var/lib/iotedge/hsm/ce…FWtFKe0_.cert.pem
  Oct 09 05:32:31 raspberrypi iotedged[24307]: 2018-10-09T14:32:31Z [ERR!] (/project/hsm-sys/azure-iot-hsm-c/src/edge_hsm_client_store.c:load_if_cert_and_key_exist_by_alias:1531) Failure when verifying certifi…ias edge_owner_ca

  workaround in following link: (for error of hsm certs)
  https://www.danielstechblog.io/azure-iot-edge-1-0-2-update-issues/
