#include "WMM_SubLibrary.c"
#include <math.h>
#include <stdexcept>


static WMMtype_MagneticModel* MagneticModel = NULL;
static WMMtype_MagneticModel* TimedMagneticModel = NULL;
static WMMtype_Ellipsoid Ellip;
static WMMtype_CoordSpherical CoordSpherical;
static WMMtype_CoordGeodetic CoordGeodetic;
static WMMtype_Date UserDate;
static WMMtype_GeoMagneticElements GeoMagneticElements;
static WMMtype_Geoid Geoid;
static bool is_initialized=false;

void geomag_free() {
	WMM_FreeMagneticModelMemory(MagneticModel);
	WMM_FreeMagneticModelMemory(TimedMagneticModel);

	free(Geoid.GeoidHeightBuffer);
	is_initialized=false;

}

double geomag_calc(double latitude,double longitude,double decimal_year,double alt_in_km) {


	/*  WMM Variable declaration  */

	if (!is_initialized)
	{
		int NumTerms = ((WMM_MAX_MODEL_DEGREES + 1) * (WMM_MAX_MODEL_DEGREES + 2) / 2 ); /* WMM_MAX_MODEL_DEGREES is defined in WMM_Header.h */

		MagneticModel = WMM_AllocateModelMemory(NumTerms); /* For storing the WMM Model parameters */
		TimedMagneticModel = WMM_AllocateModelMemory(NumTerms); /* For storing the time modified WMM Model parameters */
		if (MagneticModel == NULL || TimedMagneticModel == NULL) {

			if (MagneticModel)
				WMM_FreeMagneticModelMemory(MagneticModel);
			if (TimedMagneticModel)
				WMM_FreeMagneticModelMemory(TimedMagneticModel);
			throw std::runtime_error("internal error 1");
		}

		WMM_SetDefaults(&Ellip, MagneticModel, &Geoid); /* Set default values and constants */
		/* Check for Geographic Poles */
		//WMM_readMagneticModel_Large(filename, MagneticModel); //Uncomment this line when using the 740 model, and comment out the  WMM_readMagneticModel line.
		char fnamebuf[1024];
		const char* swfproot = getenv("SWFP_ROOT");
		if (!swfproot)
			swfproot = ".";
		snprintf(fnamebuf, sizeof(fnamebuf), "%s/fplanquick/Magnetic2010/WMM.COF", swfproot);
		WMM_readMagneticModel(fnamebuf, MagneticModel);
		WMM_InitializeGeoid(&Geoid); /* Read the Geoid file */
		/** This will compute everything needed for 1 point in time. **/
		is_initialized=true;
	}

	double maxyr = MagneticModel->epoch + 5.0;
	double minyr = MagneticModel->epoch;
	if (decimal_year>maxyr)
		decimal_year=maxyr;
	if (decimal_year<minyr)
		decimal_year=minyr;


	/* Get Coordinate prefs */
	Geoid.UseGeoid = 1; /* height above MSL */
	CoordGeodetic.lambda = longitude;
	CoordGeodetic.phi = latitude;
	CoordGeodetic.HeightAboveGeoid = alt_in_km;
	UserDate.DecimalYear = decimal_year;

	WMM_ConvertGeoidToEllipsoidHeight(&CoordGeodetic, &Geoid); /*This converts the height above mean sea level to height above the WGS-84 ellipsoid*/
	WMM_GeodeticToSpherical(Ellip, CoordGeodetic, &CoordSpherical); /*Convert from geodeitic to Spherical Equations: 17-18, WMM Technical report*/
	WMM_TimelyModifyMagneticModel(UserDate, MagneticModel, TimedMagneticModel); /* Time adjust the coefficients, Equation 19, WMM Technical report */
	WMM_Geomag(Ellip, CoordSpherical, CoordGeodetic, TimedMagneticModel,
			&GeoMagneticElements); /* Computes the geoMagnetic field elements and their time change*/

	return GeoMagneticElements.Decl;
}
#if 0
int main()
{
	printf("Geomag: %f\n",geomag_calc(59,17.5,2015.5,10));
	printf("Geomag: %f\n",geomag_calc(59,17.5,2011.5,0.01));
	printf("Geomag: %f\n",geomag_calc(59,17.5,2011.5,0.01));
	printf("Geomag: %f\n",geomag_calc(59,17.5,2011.5,0.01));
	printf("Geomag: %f\n",geomag_calc(59,17.5,2011.5,0.01));
	geomag_free();
}
#endif

