#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <unistd.h>
#include <vector>
#include <string>
#include <arpa/inet.h>
void reduce(const char* path,const char* outpath,int xsize,int ysize,int tx,int ty);


int main(int argc,char** argv)

{
    if (argc!=4)
    {
        printf("Must give three parameters: path xsize ysize\n");
        exit(1);
    }
    std::string basepath=argv[1];
    std::string inpath=basepath;
    int xsize=strtol(argv[2],NULL,10);
    int ysize=strtol(argv[3],NULL,10);
    int order=1;
    while(xsize>1)
    {
        std::string outpath;
        char buf[100];
        snprintf(buf,100,"%s-%d",basepath.c_str(),order);
        outpath=buf;        
        int destxsize=xsize/2;
        int destysize=ysize/2;
        reduce(inpath.c_str(),outpath.c_str(),xsize,ysize,destxsize,destysize);
        inpath=outpath;
        xsize=destxsize;
        ysize=destysize;
        ++order;
    }
    return 0;
}

void reduce(const char* path,const char* outpath,int xsize,int ysize,int tx,int ty)
{
    printf("Reducing %s (%dx%d) -> (%d,%d) %s\n",path,xsize,ysize,tx,ty,outpath);
    FILE* f=fopen(path,"rb");
    FILE* out=fopen(outpath,"wb");
    assert(f && out);
    std::vector<int> boxes;
    boxes.resize(xsize/2);    
    int readpixels=0;
    int y=0;
    int desty=0;
    for(y=0;y+1<ysize;)
    {   
        //double perc=100.0*double(y)/double(ysize);
        //printf("Done: %f\n",perc);
        for(int i=0;i<xsize/2;++i)
            boxes[i]=-9999;
        int numsuby=2;
        if (y==ysize-3)
            numsuby=3;
        if (numsuby!=2)    
            printf("Numsuby: %d\n",numsuby);
        for(int suby=0;suby<numsuby;++suby)
        {
            int x=0;
            for(;x+1<xsize;)
            {
                int numsubx=2;
                if (x==xsize-3)
                    numsubx=3;
                for(int subx=0;subx<numsubx;++subx)
                {
                    int xh=x/2;
                    if (xh>=xsize/2)
                        xh=xsize/2-1;
                    short height=0;
                    int ret=fread(&height,2,1,f);
                    readpixels++;
                    assert(ret);                
                    height=(short)ntohs(height);
                    //printf("Read: %d (compare (x=%d,subx=%d) to [%d]: %d)\n",height,x,subx,x/2,boxes[x/2]);
                    if (height>boxes[xh])
                        boxes[xh]=height;
                    //printf("Updated: %d\n",boxes[xh]);
                    if (height<-500)
                        printf("Height: %d\n",height);
                    if (height>6000)
                        printf("Height: %d\n",height);
                    assert(height>-500);
                    assert(height<6000);
                    ++x;
                }
            }
        }
        
        int destx=0;
        for(int i=0;i<xsize/2;++i)
        {
            short height=boxes[i];
            if (xsize<60) printf("Box height[%d,%d]:%d\n",destx,desty,height);
            height=(short)htons(height);
            int ret=fwrite(&height,2,1,out);
            ++destx;
            assert(ret);
            //int height2=(short)ntohs(height);
            //if (xsize<20)
            //    printf("Wrote height %d\n",height2);
        }
        y+=numsuby;
        assert(tx==destx);
        desty+=1;
    }
    assert(desty==ty);
    int expected_pixels=xsize*ysize;
    assert(expected_pixels==readpixels);
    //printf("Read %d pixels, expected %d\n",readpixels,expected_pixels);
    fclose(out);
    fclose(f);
    
}

