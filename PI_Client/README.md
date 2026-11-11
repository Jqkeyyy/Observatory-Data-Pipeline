This script is ran via systemd. By doing this the script client.py will run automatically if the Pi reboots.

Here are the steps I used to configure the script:


### 1. Create the service file:

```
sudo nano /etc/systemd/system/observatory-client.service
```


### 2. Add the configuration:

```
[Unit]
Description=Observatory Pi Camera Client Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/observatory/client.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

### 3. Enable and start the service:

```
sudo systemctl enable observatory-client.service
sudo systemctl start observatory-client.service
```


### 4. Verify the service is running:

I would run the once to verify the service is running then once again after a restart.

```
sudo systemctl status observatory-client.service
```