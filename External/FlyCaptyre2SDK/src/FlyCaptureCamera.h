/*
FlyCaptureCamera.h
- Shuvashis Das 03/11/2019

	This class has the functionality to:
	-	Run one FlyCapture camera
	-	Save image frames to disc
	-	Display the camera feed 

*/

#pragma once

#include "cinder/app/App.h"
#include "cinder/app/RendererGl.h"
#include "cinder/gl/gl.h"
#include "cinder/Log.h"

#include "FlyCapture2.h"


using namespace FlyCapture2;
using namespace ci;
using namespace ci::app;
using namespace std;


class FlyCaptureCamera{
public:
	FlyCaptureCamera(){};
	~FlyCaptureCamera(){ stopCamera(); };

	void 							setup();
	void 							update();
	void 							draw();

	unsigned int 					mNumCameras; 
	
	SurfaceRef						getCamSurface(){  return mCamSurface; }
	gl::TextureRef					getCamTexture() { return mCamTexture; }
	int								mFps;

private:
	void 							printBuildInfo();
	void 							printCameraInfo(CameraInfo *pCamInfo);
	void 							printError(Error error);
	void 							runSingleCamera(PGRGuid guid);
	void 							startCamera();
	void 							stopCamera();
	void							checkIfCamIsAvailable();

	FlyCapture2::Camera 			mCam;
	
	float							mLastFrameTime = 0;
	float							mCamResX;
	float							mCamResY;
	unsigned int 					mCamImageRow;
	unsigned int 					mCamImageCol;
	Error 							mError;
	SurfaceRef						mCamSurface=nullptr;
	gl::TextureRef					mCamTexture=nullptr;
	unsigned char*					mCamPixelData;
	Image							mRawImage;
	Image							mConvertedImage;
	CameraInfo						mCamInfo;



};