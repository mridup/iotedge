iotedge dev for edge-stsdk
make some experiments with azure edge modules, especially to find out if we can create a Proxy(Translation) Gateway with the Edge device and then connect non-IP devices through the gateway to the IoTHub

Issues and important points to note for RPi:
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
     
2. In such cases as point no.1, it may also happen that "Telemetry messages sent" Dashboard will not update and we are not able to see the messages from device. It is however strange that the "total number of messages used" keeps on increasing! 

3. To run module on the PY, make sure that you always specify the environment variable "OptimizeForPerformance" to "false". Set this env variable when deploying the module from the Azure Portal using "set modules" option.

4. To use devices like the BLE, we must set the network mode in the container to "host" in order for the container to access the network details. Hence we need to set the "Container Create Options" while "adding" the module in portal. Also previleged mode is set for the time being. e.g.
      {
         "NetworkingConfig": {
         "EndpointsConfig": {
            "host": {}
         }
      },
         "HostConfig": {
         "Privileged": true,
         "NetworkMode": "host"
         }
      }
      
 5. In order to run the container with root logged in, currently we are using Dockerfile without any added user (e.g. moduleuser)

 6. Make sure to always use unbuffered output in python command in dockerfile: CMD ["python", "-u", "main.py"] as python by default will always buffer the output and "docker logs <container>" will not show any logs in this case. 
So CMD ["python", "main.py"] will show no logs!
   
 7. The BLE App module(which uses the host network with root previleges) stops working after some hours (maybe around 24 hrs). basically the module looses the 'root' previledges and the module is not able to run the BLE scan network commands. There is no solution to this at this point. Only way to resolve this is:
    i) Reboot your RPi
   ii) Uninstall/Delete the module which is not running (e.g. the BLE App module above) ( Can use "Set-Modules" from Azure portal)
  iii) Re-install the same module again (again can use "Set-Modules from Azure Portal)
  
  8. EdgeHub routing of messages between modules and to/from IoT-Hub stops working after a few hours (again, happens overnight so no fixed time period when it fails). See https://github.com/Azure/iot-edge-v1/issues/619
     Only Solution so far:
     i) Re-install iotedge runtime!! (THIS IS A BIG PAIN!)
  
  
 


