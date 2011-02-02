#include <Python.h>
#include <arpa/inet.h>
#include <string>
#include "flightpath_helpers.h"

static int mega_sin_table[]={
	0, 17452, 34899, 52335, 69756, 87155, 104528, 121869, 139173, 156434, 173648, 190808, 207911, 224951, 241921, 258819, 275637, 292371, 309016, 325568, 342020, 358367, 374606, 390731, 406736, 422618, 438371, 453990, 469471, 484809, 499999, 515038, 529919, 544639, 559192, 573576, 587785, 601815, 615661, 629320, 642787, 656059, 669130, 681998, 694658, 707106, 719339, 731353, 743144, 754709, 766044, 777145, 788010, 798635, 809016, 819152, 829037, 838670, 848048, 857167, 866025, 874619, 882947, 891006, 898794, 906307, 913545, 920504, 927183, 933580, 939692, 945518, 951056, 956304, 961261, 965925, 970295, 974370, 978147, 981627, 984807, 987688, 990268, 992546, 994521, 996194, 997564, 998629, 999390, 999847, 1000000, 999847, 999390, 998629, 997564, 996194, 994521, 992546, 990268, 987688, 984807, 981627, 978147, 974370, 970295, 965925, 961261, 956304, 951056, 945518, 939692, 933580, 927183, 920504, 913545, 906307, 898794, 891006, 882947, 874619, 866025, 857167, 848048, 838670, 829037, 819152, 809016, 798635, 788010, 777145, 766044, 754709, 743144, 731353, 719339, 707106, 694658, 681998, 669130, 656059, 642787, 629320, 615661, 601815, 587785, 573576, 559192, 544639, 529919, 515038, 499999, 484809, 469471, 453990, 438371, 422618, 406736, 390731, 374606, 358367, 342020, 325568, 309016, 292371, 275637, 258819, 241921, 224951, 207911, 190808, 173648, 156434, 139173, 121869, 104528, 87155, 69756, 52335, 34899, 17452, 0, -17452, -34899, -52335, -69756, -87155, -104528, -121869, -139173, -156434, -173648, -190808, -207911, -224951, -241921, -258819, -275637, -292371, -309016, -325568, -342020, -358367, -374606, -390731, -406736, -422618, -438371, -453990, -469471, -484809, -499999, -515038, -529919, -544639, -559192, -573576, -587785, -601815, -615661, -629320, -642787, -656059, -669130, -681998, -694658, -707106, -719339, -731353, -743144, -754709, -766044, -777145, -788010, -798635, -809016, -819152, -829037, -838670, -848048, -857167, -866025, -874619, -882947, -891006, -898794, -906307, -913545, -920504, -927183, -933580, -939692, -945518, -951056, -956304, -961261, -965925, -970295, -974370, -978147, -981627, -984807, -987688, -990268, -992546, -994521, -996194, -997564, -998629, -999390, -999847, -1000000, -999847, -999390, -998629, -997564, -996194, -994521, -992546, -990268, -987688, -984807, -981627, -978147, -974370, -970295, -965925, -961261, -956304, -951056, -945518, -939692, -933580, -927183, -920504, -913545, -906307, -898794, -891006, -882947, -874619, -866025, -857167, -848048, -838670, -829037, -819152, -809016, -798635, -788010, -777145, -766044, -754709, -743144, -731353, -719339, -707106, -694658, -681998, -669130, -656059, -642787, -629320, -615661, -601815, -587785, -573576, -559192, -544639, -529919, -515038, -500000, -484809, -469471, -453990, -438371, -422618, -406736, -390731, -374606, -358367, -342020, -325568, -309016, -292371, -275637, -258819, -241921, -224951, -207911, -190808, -173648, -156434, -139173, -121869, -104528, -87155, -69756, -52335, -34899, -17452, 0
};

class Chunk {
public:
	iMerc start17;
	long startstamp;
	iMerc last17;
	int lasthdg;
	int lastrate;
	int lastturn;
	int lastalt;
	long laststamp;
	int laststampdelta;
	long distance_millinm;
	bool finished;
	BinaryCodeBuf binbuf;
	iMerc real_endpos;
	long real_endstamp;
	int real_endalt;
	int version;


	Chunk() {
		startstamp = lasthdg = lastrate = lastalt = lastturn = laststamp = laststampdelta
				= distance_millinm = version = 0;
		finished = 0;
	}
	long getStartStamp() {
		return startstamp;
	}
	long getEndStamp() {
		return laststamp;
	}
	float getDistance() {
		return distance_millinm / 1000.0f;
	}
	void deserialize(const std::string& inbuf,int version) {
		BufReader data(inbuf);

		start17.deserialize(data);
		startstamp = data.readLong();
		last17.deserialize(data);
		lasthdg = data.readInt();
		lastrate = data.readInt();
		if (version>=3)
			lastalt = data.readInt();
		lastturn = data.readInt();
		laststamp = data.readLong();
		//printf("Deserialized stamp: %ld\n",laststamp/1000);
		laststampdelta = data.readInt();
		real_endpos=last17;
		real_endstamp=laststamp;
		real_endalt=lastalt;
		finished = data.readInt() != 0;

		this->version=version;
		if (version > 1)
			distance_millinm = data.readLong();
		else
			distance_millinm = 0;
		//printf("Read distance: %f\n",distance_millinm/1000.0);
		//printf("Read finished: %d\n",(int)finished);
		binbuf.init_from(data);
		last17 = start17;
		lasthdg = 0;
		lastturn = 0;
		lastrate = 50;

		lastalt=0;
		laststamp = startstamp;
		laststampdelta = 1000;

	}

	PyObject* playback() {
		//printf("Playback, bits left: %d\n",binbuf.avail());
		if (binbuf.avail()<=0)
		{
			return NULL;
		}
		long raw_stampdelta = binbuf.gammadecode();
		long raw_turn = binbuf.gammadecode();
		long raw_rate = binbuf.gammadecode();
		if (version>=3)
		{
			long raw_alt = binbuf.gammadecode();
			lastalt+=raw_alt;
		}
		laststampdelta += raw_stampdelta;
		long code_turn = raw_turn;
		long code_rate = lastrate + raw_rate;

		lastrate = (int) code_rate;
		lastturn = (int) (code_turn);
		lasthdg += code_turn;
		laststamp += laststampdelta;
		last17 = travel(last17, lastrate, lasthdg,
				laststampdelta);

		if (binbuf.avail()<=0)
		{
			if (laststamp!=real_endstamp)
				throw std::runtime_error("Internal error - laststamp after finishing playback is not identical to expected endstamp");
			if (real_endpos.x!=last17.x ||
				real_endpos.y!=last17.y)
				throw std::runtime_error("Internal error - last17 after finishing playback is not identical to expected endpos");
			if (real_endalt!=lastalt)
				throw std::runtime_error("Internal error - last altitude after finishing playback is not identical to expected alt");
			//printf("New alt coding worked beautifully: %d %d",real_endalt,lastalt);
		}
		/*
		PosTime item = new PosTime();
		item.pos = last17.copy();
		item.stamp = laststamp;
		*/
		PyObject* postup=PyTuple_New(2);
		PyTuple_SET_ITEM(postup,0,PyInt_FromLong(last17.x));
		PyTuple_SET_ITEM(postup,1,PyInt_FromLong(last17.y));

		PyObject* tup=PyTuple_New(3);
		PyTuple_SET_ITEM(tup,0,postup);
		PyTuple_SET_ITEM(tup,1,PyInt_FromLong(laststamp));
		PyTuple_SET_ITEM(tup,2,PyInt_FromLong(25*lastalt));


		return tup;
	}
	iMerc travel(iMerc pos, int rate, int hdg, int delta) {
		/*
		float rad = (float) (hdg / (180.0f / M_PI));
		int dx = (int) (delta * rate * (sin(rad)) / 1000.0f);
		int dy = (int) (delta * rate * (-cos(rad)) / 1000.0f);

		return iMerc(pos.x + dx, pos.y + dy);
		*/

		long megasin=mega_sin_table[hdg];
		long megacos=-mega_sin_table[(hdg+90)%360];

		int dx=(int)((delta*rate*megasin)/1000000000L);
		int dy=(int)((delta*rate*megacos)/1000000000L);

		return iMerc(pos.x + dx, pos.y + dy);
	}
};

void set_long(PyObject* d,const char* key,long val)
{
	PyObject* py=PyLong_FromLong(val);
	PyDict_SetItemString(d,key,py);
	Py_DECREF(py);
}
void set_float(PyObject* d,const char* key,double val)
{
	PyObject* py=PyFloat_FromDouble(val);
	PyDict_SetItemString(d,key,py);
	Py_DECREF(py);
}
void set_pos(PyObject* d,const char* key,iMerc val)
{
	PyObject* py=PyTuple_New(2);
	PyTuple_SET_ITEM(py,0,PyInt_FromLong(val.x));
	PyTuple_SET_ITEM(py,1,PyInt_FromLong(val.y));
	PyDict_SetItemString(d,key,py);
	Py_DECREF(py);
}

PyObject* decode_flightpath(const std::string& buf,int version)
{
	Chunk chunk;
	chunk.deserialize(buf,version);
	PyObject* d=PyDict_New();
	/*
	startstamp=path['startstamp']
	endstamp=path['endstamp']
	startpos=path['startpos']
	endpos=path['endpos']
	distance=path['distance']
	path=path['path']
	 *
	 */

	PyObject* thelist=PyList_New(0);
	for(;;)
	{
		PyObject* item=chunk.playback();
		if (item==NULL)
			break;
		PyList_Append(thelist,item);
	}
	set_long(d,"startstamp",chunk.startstamp);
	set_long(d,"endstamp",chunk.real_endstamp);
	set_pos(d,"startpos",chunk.start17);
	set_pos(d,"endpos",chunk.real_endpos);
	set_float(d,"distance",chunk.distance_millinm/1000.0);

	PyDict_SetItemString(d,"path",thelist);
	Py_DECREF(thelist);
	return d;
}

