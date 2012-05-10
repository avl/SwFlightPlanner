#include <math.h>
#include <string>
#include <arpa/inet.h>
#include <stdio.h>
#include <vector>

void colorfun(unsigned int height,unsigned char& r,unsigned char& g,unsigned char& b)
{
    int c=height/3;
    if (c==0)
    {
        r=g=0;
        b=255;
        return;
    }
    if (c<256)
    {
        g=c;r=b=0;
        return;        
    }
    c-=255;
    if (c<256)
    {
        g=255;r=c;b=0;
        return;        
    }
    c-=255;
    if (c<256)
    {
        g=255-c;r=255;b=0;
        return;        
    }
    c-=255;
    c/=2;
    if (c<256)
    {
        b=g=c;r=255;
        return;        
    }
    c-=256;
    c/=12;	
    b=255;
    if (c<128)
    {
    	r=255-c;
    	g=255-c;
    	return;
    }
	r=128;g=128;b=255;    
    return;
}

std::string colorize_combine_heightmap(std::vector<std::string>& arr)
{
    std::string ret;
    unsigned char* out=new unsigned char[256*256*3];
    try{
        //float d=2000.0/256.0;
        int idx=0;
        for(int y=0;y<256;y+=256)
        {
            for(int x=0;x<256;x+=256)
            {
            	//printf("Indexing into array of length %d, index %d\n",(int)arr.size(),idx);
                std::string& s=arr[idx];
                if (s.length()!=2*256*256)
                    return "";
                const char* buf=s.data();
                const short* elev=(const short*)buf;
                const short* elev_end=elev+256*256;
                unsigned char* outp=out+x*3+256*3*y;
                for(int i=0;i<256;++i)
                {
                    for(int j=0;j<256;++j)
                    {
                        int height=ntohs(*elev);
                        if (height<0 || height>20000) height=0;
                        elev+=1;
                        colorfun(height,outp[0],outp[1],outp[2]);
                        outp+=3;
                    }
                    //outp+=(256*3)*3;
                }
                if (elev!=elev_end) return "";
                ++idx;            
            }
        }
        ret.assign((const char*)out,256*256*3);
    	//printf("Assigning return\n");
        
    }
    catch(...)
    {
        delete [] out;
        throw;
    }
    delete [] out;
    return ret;
}


