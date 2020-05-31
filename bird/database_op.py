import os

import django
os.environ.setdefault('DJANGO_SETTING_MODULE', 'birdidentification.settings')
django.setup()
from bird import models
def main():
    f1=open("../dataset/output.txt",'r')
    lines=f1.readlines()
    for line in lines:
        dataList=str(line).split()
        models.All_Bird.objects.create(sci_name=str(dataList[2]+' '+dataList[3]),
                                              name=str(dataList[1]),
                                              pos=str(dataList[4]),
                                               )
        print(dataList[2]+' '+dataList[3])

if __name__ == '__main__':
    main()