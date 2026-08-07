#include "cinder/app/App.h"
#include "cinder/app/RendererGl.h"
#include "cinder/gl/gl.h"

#include "FlyCaptureCamera.h"

using namespace ci;
using namespace ci::app;
using namespace std;

class SimpleFlyCaptureApp : public App {
  public:
	void setup() override;
	void update() override;
	void draw() override;

	FlyCaptureCamera		mFlyCaptureCamera;
	bool					mFlyCaptureConnected=false;
};

void SimpleFlyCaptureApp::setup()
{
	mFlyCaptureCamera.setup();
	if (mFlyCaptureCamera.mNumCameras > 0) {
		mFlyCaptureConnected = true;
		CI_LOG_I("Number of connected FlyCapture Camera " << mFlyCaptureCamera.mNumCameras);
	}
	else {
		CI_LOG_I("No Fly Capture cameras detected");
	}
}

void SimpleFlyCaptureApp::update()
{
	if (mFlyCaptureConnected) {
		mFlyCaptureCamera.update();
	}
}

void SimpleFlyCaptureApp::draw()
{
	gl::clear( Color( 0, 1, 0 ) );
	if (mFlyCaptureConnected) {
		gl::draw(mFlyCaptureCamera.getCamTexture());
	}
}

CINDER_APP( SimpleFlyCaptureApp, RendererGl )
