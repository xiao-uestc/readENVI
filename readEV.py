'''
https://github.com/xiao-uestc
'''

import numpy as np
import re
import struct
import matplotlib.pyplot as plt
import os
import random
import math
import csv


def readhdr(hdr_path):
    hdr = {}
    with open(hdr_path,'rb') as f:
        while True:
            content = str(f.readline(),'utf-8')
            if not content:
                break
            else:
                if re.match('samp',content):
                    hdr['samps'] = re.search('samp.*=(.*)',content).group(1).strip()
                elif re.match('line',content):
                    hdr['lines'] = re.search('line.*=(.*)',content).group(1).strip()
                elif re.match('bands',content):
                    hdr['bands'] = re.search('band.*=(.*)',content).group(1).strip()
                elif re.match('data type', content):
                    hdr['dtype'] = re.search('data.*=(.*)',content).group(1).strip()
                elif re.match('inter', content):                                            
                    hdr['interleave'] = re.search('inter.*=(.*)',content).group(1).strip()
                elif re.match('header', content):
                    hdr['headoffset'] = re.search('head.*=(.*)',content).group(1).strip()
                elif re.match('map', content):
                    hdr['mapinfo'] = re.search('map info =(.*)',content).group(1).strip()
                elif re.match('coordinate', content):
                    hdr['coordinate'] = re.search('coordinate.*=(.*)', content).group(1).strip()
                elif re.match('data ignore', content):
                    hdr['dataignore'] = re.search('data.*=(.*)',content).group(1).strip()
    return hdr     

def read_envi(img_path, hdr):
    #仅针对存储格式为bsq Only for storage format bsq

    '''
    int16 uint16  2 字节
    float         4 字节
    int32 uint32  4 字节
    double        8 字节
    numpy 只有 float32 float64 | float 即为 float32 | double 即为 float64
    dtype = 5: double  4:float  3:int32  2:int16  12:uint16  13:uint32

    ENVI 与 TIFF 两种格式
    根据图像大小计算是否一次读取完 Calculate according to the size of the image whether to read it all at once
    '''
    bands = int(hdr['bands'])
    lines = int(hdr['lines'])
    samps = int(hdr['samps'])
    datatype = int(hdr['dtype'])
    typedict = {2:'int16',3:'int32',4:'float32',5:'flaot64',12:'uint16',13:'uint32'}
    bytedict = {2:2,3:4,4:4,5:8,12:2,13:4}
    dtypedict = {2:'h',3:'i',4:'f',5:'d',12:'H',13:'I'}
    print("-----正在读取数据-----",end = '\r')
    with open(img_path,'rb') as f:
        data = np.zeros([lines,samps,bands],dtype = typedict[datatype])
        for i in range(bands):
            for j in range(lines):
                a = f.read(bytedict[datatype] * samps)
                data[j,:,i] = struct.unpack(str(samps) + dtypedict[datatype],a)
    print("-----数据读取完成-----",end = '\r')
    return data

def read_data(dir_path):
    all_file_list =[]
    filelist = os.listdir(dir_path)
    for file in filelist:
        filename = os.path.join(dir_path,file)
        if os.path.isdir(filename):
            get_all_filepath(filename)
        else:
            suffix = os.path.splitext(filename)[1]
            #print(suffix)
            if suffix ==".hdr":
                all_file_list.append(filename)
    for hdr_path in all_file_list:
        hdr = readhdr(hdr_path)
        envifile = hdr_path.split('.')[0]+'.dat'
        # xlname = hdr_path.split('.')[0]+'.xls'
        bands = int(hdr['bands'])
        lines = int(hdr['lines'])
        samps = int(hdr['samps'])
        data = read_envi(envifile,hdr)
        data[data < 0 ] = 0

        save_envi(envifile,data)


def wxlrd(xpath,data):
    # 待存储数据 Data to be stored
    wb = openpyxl.load_workbook(xpath)
    ws = wb.create_sheet("Mysheet")
    r,c = data.shape
    for i in range(r):
        for j in range(c):
            ws.cell(r+1,c+1).value = data[i][j]
    wb.save(xpath)


def wcsvs(csv_path,data):
    with open(csv_path,'w',encoding='utf-8-sig',newline='') as f:
        csvwriter = csv.writer(f)
        for i in range(len(data)):
            csvwriter.writerow(data[i])

def savehdr(save_path,hdr):
    hdr_path = save_path.split(".")[0] + '.hdr'
    with open(hdr_path, 'wb') as f:
        f.write(b"ENVI\n")
        temp = "samples = " + hdr['samps'] + '\n'
        f.write(str.encode(temp))
        temp = "lines   = " + hdr['lines'] + '\n'
        f.write(str.encode(temp))
        temp = "bands   = " + hdr['bands'] + '\n'
        f.write(str.encode(temp))
        if 'headoffset' in hdr:
            temp = "header offset = " + hdr['headoffset'] + '\n'
            f.write(str.encode(temp))
        f.write(b"file type = ENVI Standard\n")
        if 'dtype' in hdr:
            temp = "data type = " + hdr['dtype'] + '\n'
            f.write(str.encode(temp))
        if 'interleave' in hdr:
            temp = "interleave = " + hdr['interleave'] + '\n'
            f.write(str.encode(temp))
        if 'mapinfo' in hdr:
            temp = "map info = " + hdr['mapinfo'] + '\n'
            f.write(str.encode(temp))
        if 'coordiname' in hdr:
            temp = "coordinate system string = " + hdr['coordinate'] + '\n'
            f.write(str.encode(temp))
        if 'dataignore' in hdr:
            temp = "data ignore value = " + hdr['dataignore'] + '\n'
            f.write(str.encode(temp))


def save_envi(filename,data,hdr):
    # 仅针对存储格式为bsq Only for storage format bsq
    print("-----正在保存数据-----", end='\r')
    typedict = {'int16':2,'int32':3,'int64':3,'float32':4,'flaot64':5,'uint16':12,'uint32':13}
    bytedict = {2:2,3:4,4:4,5:8,12:2,13:4}
    dtypedict = {2:'h',3:'i',4:'f',5:'d',12:'H',13:'I'}
    dtype = data.dtype
    if dtype == 'int64':
        data = data.astype('int32')
    filename = filename.split(".")[0] + '.dat'
    if len(data.shape) == 2:
        lines,samps = data.shape
        bands = 1
    elif len(data.shape) == 3:
        lines,samps,bands = data.shape
    hdr['lines'] = str(lines)
    hdr['samps'] = str(samps)
    hdr['bands'] = str(bands)
    hdr['dtype'] = str(typedict[str(dtype)])
    savehdr(filename,hdr)
    with open(filename, "wb") as f:
        if bands > 1:
            for i in range(bands):
                for j in range(lines):
                    datai = struct.pack(str(samps) + dtypedict[typedict[str(dtype)]],*data[j,:,i])
                    f.write(datai)
        else :
            for j in range(lines):
                datai = struct.pack(str(samps) + dtypedict[typedict[str(dtype)]], *data[j, :])
                f.write(datai)
    print("-----数据保存完成-----",end = '\r')


def main():
    # 保存出小于的文件
    # 输入所有文件所在文件夹路径 Enter the path of the folder where all files are located
    # read_data(r"E:\1")



    end_data,hdr = flt_data()
    file_path = r'J:新建文件夹\new.dat'
    save_envi(file_path,end_data.reshape(-1,4),hdr)



    # 读取单个envi Read a single envi
    #    hdr_path = r"C:\Users\XIAO\Desktop\11111\f131.hdr"
    #    img_path = r"C:\Users\XIAO\Desktop\11111\f131.dat"
    #    hdr = readhdr(hdr_path)
    #    bands = int(hdr['bands'])
    #    lines = int(hdr['lines'])
    #    samps = int(hdr['samps'])
    #    data = read_envi(img_path,bands,lines,samps,'float32')
    #    print(data.shape)


    # 显示数据第一个波段 Display the first band of data
    # plt.imshow(data[:,:,0])
    # plt.show()


if __name__ == '__main__':
    main()
