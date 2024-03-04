
# Intro

This is a proof-of-concept where we show that python can generate high quality audio pulses so they become synthesizer clock sync pulses. We are testing this code with sync-in port on Korg Volcas:

* https://www.korg-volca.com/en/

The code can handle up to 4 audio cards. This means that we can handle sync-in on up to 4 synthesizer independently and yet synchronized. This is an improvement over the Korg provided daisy chaining of the sync-in-sync-out ports.

# Functionality

We want to be able to stop, start and pause patches independently on 4 synthesizers without loosing the track of the position in the patch. This way we can switch between memorized patches while the synthesizer is in a stop or pause state. The music stops and pause on step 16 of a patch and starts again on step 1. This way even if we stop and start different synthesizers independently they all remain at the same step in their respective patches.

In addition, we can change tempo on all synthesizer in a synchronous way. This means that we first set desire tempo and wait until all synthesizers reach step 16. Tempo always changes with the first step.

Finally, we added a "step" functionality when sync clock is stopped on a given synthesizer. This is especially helpful for Korg Volca Keys that does not have a step record functionality. This should be used carefully if one wants all synthesizers to remain on the same step.

# Hardware

We initially deployed the code on Raspberry Pi 3 and 4 without much success. They can only handle 1 or 2 USB Audio cards. That's why we decided to go with an overclocked Jetson Nano board. Here is the list of all components used in this proof-of-concept:

* Jetson Nano https://www.amazon.com/gp/product/B084DSDDLT
* USB Hub https://www.amazon.com/gp/product/B07M63G6FH
* USB Male to USB Male cable https://www.amazon.com/gp/product/B07KJ96M2W
* 7in LCD Screen https://www.amazon.com/gp/product/B07L6WT77H
* USB Audio Adapters https://www.amazon.com/gp/product/B0BZPC4JW5
* 12 Keys and 3 Knobs Keyboard https://a.aliexpress.com/_msKgWZ4
* SD Card
* 2 x Power Supply 5V 2.5A
* HDMI Cable

Optional items:

* Nylon Nuts and Bolts https://www.amazon.com/gp/product/B07JYSFMRY
* Plexiglass
* 2.5 mm Drill Bit
* 2.5 mm Zip Ties

In order to install the software on the Jetson Nano, you will need mouse, keyboard and access to internet either through USB WiFi dongle or through Ethernet cable. Internet will not be needed after the software is installed and it is working.

# Operating System

Official Jetson Nano operating system has still Ubuntu 18.04. That's why we found this unofficial Ubuntu 20.04 operating system:

* https://github.com/Qengineering/Jetson-Nano-Ubuntu-20-image

It already comes with overclocked CPUs. We are not using GPU for this project.

# Software

Once the Jetson Nano is up and running, we have to connect it to a local internet, write down the IP address, and run this script:

```shell
IP="192.168.8.228" scripts/deploy_code.sh
```

Then we log into the Jetson Nano as "jetson" user (same password) and we run the following install script:

```shell
ssh jetson@192.168.8.228
sudo ~/pulse_generator/scripts/install.sh
```

The installation process reboots the Jetson Nano to terminal auto-login and runs the python code when executing the 'bashrc' file.

# Final 

![Alt text](images/IMG_7476.jpg?raw=true "Title")

