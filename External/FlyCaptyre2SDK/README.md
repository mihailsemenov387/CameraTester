Cinder-FlyCapture
===================
Cinder block for integrating [Point Grey Research / Flir] FlyCapture SDK

##### Adding this block to Cinder
This block was built with version 0.9.1, so 0.9.0 and up should work. This block is also only available on Windows since the FlyCapture SDK is Windows only. The SDK can also be used on Mac OSX using ```libdc1394```, however this block currently doesn't have that support. The latest/last Fly Capture SDK also only contains .dll files for x64 + toolset v140.

* First get a camera that uses the FlyCapture SDK (which might be tricky since most/all cameras that use the SDK have been discontinued), this block was built with a Point Grey [FireFly MV](https://www.visiononline.org/product-catalog-detail.cfm/FLIR-Systems-Inc/1-3-MP-Firefly-MV-USB-2-0-Camera/productid/3251) 0.3MP B&W. It looks like newer versions of the Firefly will use the Flir Spinnaker SDK instead.
* Second, download the [FlyCapture SDK](https://www.flir.com/products/flycapture-sdk/)
  - Also available from [here](https://flir.app.boxcn.net/v/Flycapture2SDK)
  - This block was built with SDK v 2.13.3.61_x64 but should work with newer versions as well
  - Some of the lib files are also included in this block repo, but installing the SDK also includes several samples of the code base and a sample preview app for testing cameras outside of Cinder
* Add this block to your Cinder/blocks folder
* Use TinderBox and create a new Cinder project

There is a sample project included with the block.

##### Tips and Gotchas
- The resolution and frame rate is hard coded to 640x480 30 fps, if your camera doesn't support those settings there may be complications.
- The ```camera.RetrieveBuffer``` method is blocking so the camera update does it's own check for new frames on the same thread. This allows your app fps to be faster than the camera fps.

##### TODOS
- add configuration options, auto_exposure, fps, resolution
- consider changing the update method + ```mLastFrameTime``` checks for when to get a new frame

License
-------
Copyright (c) 2019, Red Paper Heart, All rights reserved. To contact Red Paper Heart, email hello@redpaperheart.com or tweet @redpaperhearts

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 
Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
