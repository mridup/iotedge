To run module on the PY, make sure that you always specify the environment variable "OptimizeForPerformance" to "false".
Set this env variable when deploying the module from the Azure Portal using "set modules" option.

To send a message from outside the docker container using the cmdline python script:
docker exec pitempsensor /bin/bash -c "python cmdline.py run_module"


