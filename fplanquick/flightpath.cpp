#include <Python.h>
#include <arpa/inet.h>
#include <string>
#include "flightpath_helpers.h"
class Chunk {
public:
	iMerc start17;
	long startstamp;
	iMerc last17;
	int lasthdg;
	int lastrate;
	int lastturn;
	long laststamp;
	int laststampdelta;
	long distance_millinm;
	bool finished;
	BinaryCodeBuf binbuf;


	Chunk() {
		startstamp = lasthdg = lastrate = lastturn = laststamp = laststampdelta
				= distance_millinm = finished = 0;
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
		lastturn = data.readInt();
		laststamp = data.readLong();
		laststampdelta = data.readInt();
		finished = data.readInt() != 0;

		if (version > 1)
			distance_millinm = data.readLong();
		else
			distance_millinm = 0;
		printf("Read distance: %f\n",distance_millinm/1000.0);
		printf("Read finished: %d\n",(int)finished);
		binbuf.init_from(data);
		last17 = start17;
		lasthdg = 0;
		lastturn = 0;
		lastrate = 50;
		laststamp = startstamp;
		laststampdelta = 1000;

	}

	PyObject* playback() {
		printf("Playback, bits left: %d\n",binbuf.avail());
		if (binbuf.avail()<=0)
		{
			return NULL;
		}
		long raw_stampdelta = binbuf.gammadecode();
		long raw_turn = binbuf.gammadecode();
		long raw_rate = binbuf.gammadecode();
		laststampdelta += raw_stampdelta;
		long code_turn = raw_turn;
		long code_rate = lastrate + raw_rate;

		lastrate = (int) code_rate;
		lastturn = (int) (code_turn);
		lasthdg += code_turn;
		laststamp += laststampdelta;
		last17 = travel(last17, lastrate, lasthdg,
				laststampdelta);

		/*
		PosTime item = new PosTime();
		item.pos = last17.copy();
		item.stamp = laststamp;
		*/
		PyObject* postup=PyTuple_New(2);
		PyTuple_SET_ITEM(postup,0,PyInt_FromLong(last17.x));
		PyTuple_SET_ITEM(postup,1,PyInt_FromLong(last17.y));

		PyObject* tup=PyTuple_New(2);
		PyTuple_SET_ITEM(tup,0,postup);
		PyTuple_SET_ITEM(tup,1,PyInt_FromLong(laststamp));

		return tup;
	}
	iMerc travel(iMerc pos, int rate, int hdg, int delta) {
		float rad = (float) (hdg / (180.0f / M_PI));
		int dx = (int) (delta * rate * (sin(rad)) / 1000.0f);
		int dy = (int) (delta * rate * (-cos(rad)) / 1000.0f);

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
	set_long(d,"startstamp",chunk.startstamp);
	set_long(d,"endstamp",chunk.laststamp);
	set_pos(d,"startpos",chunk.start17);
	set_pos(d,"endpos",chunk.last17);
	set_float(d,"distance",chunk.distance_millinm/1000.0);


	PyObject* thelist=PyList_New(0);
	for(;;)
	{
		PyObject* item=chunk.playback();
		if (item==NULL)
			break;
		PyList_Append(thelist,item);
	}
	PyDict_SetItemString(d,"path",thelist);
	Py_DECREF(thelist);
	return d;
}

