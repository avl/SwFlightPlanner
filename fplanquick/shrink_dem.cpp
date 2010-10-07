#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <unistd.h>
#include <vector>
#include <string>
#include <arpa/inet.h>
void reduce(const char* path,const char* outpath,int xsize,int ysize,int tx,int ty,bool outer);


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
    bool outer=true;
    while(xsize>1)
    {
        std::string outpath;
        char buf[100];
        snprintf(buf,100,"%s-M%d",basepath.c_str(),order); //M for Min-Max
        outpath=buf;        
        int destxsize=xsize/2;
        int destysize=ysize/2;
        reduce(inpath.c_str(),outpath.c_str(),xsize,ysize,destxsize,destysize,outer);
        outer=false;
        inpath=outpath;
        xsize=destxsize;
        ysize=destysize;
        ++order;
    }
    return 0;
}

void reduce(const char* path,const char* outpath,int xsize,int ysize,int tx,int ty,bool outer)
{
    printf("Reducing %s (%dx%d) -> (%d,%d) %s\n",path,xsize,ysize,tx,ty,outpath);
    FILE* f=fopen(path,"rb");
    FILE* out=fopen(outpath,"wb");
    assert(f && out);
    std::vector<int> minboxes;
    minboxes.resize(xsize/2);    
    std::vector<int> maxboxes;
    maxboxes.resize(xsize/2);    
    int readpixels=0;
    int y=0;
    int desty=0;
    for(y=0;y+1<ysize;)
    {   
        //double perc=100.0*double(y)/double(ysize);
        //printf("Done: %f\n",perc);
        for(int i=0;i<xsize/2;++i)
        {
            minboxes[i]=32000;
            maxboxes[i]=-32000;
        }
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
                    short minheight=0;
                    int ret=fread(&minheight,2,1,f);
                    assert(ret);
                    short maxheight=0;
                    if (outer)
                    {
                        maxheight=minheight;
                    }
                    else
                    {
                        int ret=fread(&maxheight,2,1,f);
                        assert(ret);
                    }
                    readpixels++;
                    assert(ret);                
                    minheight=(short)ntohs(minheight);
                    maxheight=(short)ntohs(maxheight);
                    //printf("Read: %d (compare (x=%d,subx=%d) to [%d]: %d)\n",height,x,subx,x/2,boxes[x/2]);
                    if (maxheight>maxboxes[xh])
                        maxboxes[xh]=maxheight;
                    if (minheight<minboxes[xh])
                        minboxes[xh]=minheight;
                    //printf("Updated: %d\n",boxes[xh]);
                    if (minheight<-500)
                        printf("Height: %d\n",minheight);
                    if (maxheight>6000)
                        printf("Height: %d\n",maxheight);
                    assert(minheight>-500);
                    assert(maxheight<6000);
                    ++x;
                }
            }
        }
        
        int destx=0;
        for(int i=0;i<xsize/2;++i)
        {
            short minheight=minboxes[i];
            short maxheight=maxboxes[i];
            if (xsize<60) printf("Box height[%d,%d]:min=%d,max=%d\n",destx,desty,minheight,maxheight);
            minheight=(short)htons(minheight);
            maxheight=(short)htons(maxheight);
            int ret=fwrite(&minheight,2,1,out);
            assert(ret);
            ret=fwrite(&maxheight,2,1,out);
            assert(ret);
            ++destx;
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

