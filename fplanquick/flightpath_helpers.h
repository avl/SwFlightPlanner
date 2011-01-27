#ifndef FLIGHTPATH_HELPERS_INCLUDED
#define FLIGHTPATH_HELPERS_INCLUDED

#include <arpa/inet.h>
#include <string>
#include <stdexcept>
#include <stdlib.h>
#include <endian.h>
#include <string.h>
#include <bitset>
#include <vector>

class BufReader {
	std::string data;
	int p;
public:
	BufReader(const std::string& data) :
		data(data), p(0) {
	}
	int avail()
	{
		return data.length()-p;
	}
	void read_raw(char* dest,int len)
	{
		int avail=data.length()-p;
		if (len<0 || len>avail)
			throw new std::runtime_error("Bad len");
		memcpy(dest,data.data()+p,len);
		p+=len;
	}
	int readInt() {
		if (p + 4 > (int)data.length())
			throw std::runtime_error("No int left to read");
		int ret = 0;
		memcpy(&ret, data.data()+p, 4);
		ret=ntohl(ret);
		p += 4;
		return ret;
	}
	int readLong() {
		if (p + 8 > (int)data.length())
			throw std::runtime_error("No int left to read");
		int64_t ret = 0;
		memcpy(&ret, data.data()+p, 8);
		ret = be64toh(ret);
		p += 8;
		return ret;
	}
};
class BitSeq {
	int len;
	std::bitset<64> bits;
public:
	BitSeq() {
		bits = 0;
		len = 0;
	}
	void setsingle(bool v) {
		len = 1;
		bits[0] = v;
	}
	void unarycode(long minbits_) {
		if (minbits_ < 0 || minbits_ >=63)
			throw std::runtime_error("Bad unarycode value:");
		int minbits = (int) minbits_;
		len = minbits + 1;
		for (int i = 0; i < minbits; ++i)
			bits[i] = true;
		bits[minbits] = false;
	}
	static int countbits(long number) {
		if (number < 0)
			throw std::runtime_error(
					"Don't know how to count bits of a negative number");

		for (int bits = 0; bits < 64; ++bits) {
			long l = 1;
			l <<= bits;
			if (number < l)
				return bits;
		}
		return 64;
	}

	void binarycode(long number, int numbits) {
		if (countbits(number) != numbits)
			throw std::runtime_error("Number is not ideally represented with N bits");
		if (numbits <= 0) {
			len = 0;
			return;
		}
		len = numbits - 1;
		for (int i = 0; i < numbits - 1; ++i) {
			bool b = (number & (1l << i)) != 0;
			bits[i] = b;
		}
	}
	int size() {
		return len;
	}
	bool getBit(int i) {
		return bits[i];
	}
	void setBit(int i, bool b) {
		bits[i] = b;
	}
	void setSize(int len2) {
		len = len2;
	}
	bool getsingle() {
		return bits[0];
	}
	long binarydecode(int plen) {
		plen -= 1;
		if (plen > len)
			throw std::runtime_error("Internal");
		if (plen < 0)
			return 0;
		long number = 0;
		for (int i = 0; i < plen; ++i) {
			if (bits[i])
				number |= (1l << i);
		}
		number |= (1l << plen);
		return number;
	}
};

class BinaryCodeBuf {
	std::vector<int> bits;
	int idx;
	int off;
	int size;
	BitSeq seq1;
	BitSeq seq2;
	BitSeq seq3;
	BitSeq seq4;
	BitSeq seq5;
public:
	int avail()
	{
		return size-(idx*32+off);
	}
	void init_from(BufReader& buf)
	{
		int len=buf.readInt();
		printf("len field=%d (tot buf len: %d)\n",len,buf.avail());
		size=buf.readInt();
		printf("Size: %d bits\n",size);
		bits.resize(len);
		buf.read_raw((char*)(bits.data()),4*len);
		for(int i=0;i<len;++i)
		{
			bits[i]=ntohl(bits[i]);
		}
		printf("Read buf. Now avail: %d\n",buf.avail());
		int magic=buf.readInt();
		if (magic!=0xfeed42)
			throw std::runtime_error("Bad magic in fphelper");
		idx=0;
		off=0;
		printf("BinaryCodeBUf init complete\n");
	}
	bool read(BitSeq& seq, int len) {
		int bitlen = idx * 32 + off;
		if (bitlen + len > size)
			return false;

		seq.setSize(len);
		for (int i = 0; i < len; ++i) {
			bool b = (bits[idx] & (1 << off)) != 0;
			seq.setBit(i, b);
			off += 1;
			if (off == 32) {
				off = 0;
				idx += 1;
			}
		}
		return true;
	}

	bool readbit() {
		int bitlen = idx * 32 + off;
		if (bitlen >= size)
			throw std::runtime_error("Out of bits");

		bool b = (bits[idx] & (1 << off)) != 0;
		printf("  Decode single bit: %d\n",(int)b);
		off += 1;
		if (off == 32) {
			off = 0;
			idx += 1;
		}
		return b;
	}
	long gammadecode() {
		if (!readbit())
		{
			printf("Read gammacoded: 0\n");
			return 0;
		}
		bool negative = false;
		if (readbit())
			negative = true;
		int bitsbits = 0;
		while (readbit() == true)
			++bitsbits;
		read(seq4, bitsbits - 1);
		int bits = (int) seq4.binarydecode(bitsbits);
		read(seq5, bits - 1);
		long x = seq5.binarydecode(bits);
		++x;
		if (negative)
			x = -x;
		printf("Read gammacoded: %ld\n",(long)x);
		return x;
	}

};

struct iMerc {
	int x, y;
	iMerc() {
		x = y = 0;
	}
	iMerc(int x_, int y_) {
		x = x_;
		y = y_;
	}
	void deserialize(BufReader& r) {
		x = r.readInt();
		y = r.readInt();
	}
};

#endif
