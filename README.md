<div align="center">
  
# Modern_Gent_Trendsetter
<img width="300" alt="image" src="https://github.com/kkms-14/Modern_Gent_Trendsetter/assets/74400595/c25e80fb-86d2-4c95-b013-3de6ee55c602">
</div>

## Group member:
* CAI Yongjie 1155158879
* HUANG Huangmei 1155142720
* Li Ze 1155157157
* WANG Yutao 1155157060
## Overview
This website is an online mall. It is based on Django framework in python and Jinja2 for frontend. We have implemented user registration, user login, product search, product details, add shopping cart, product payment and so on. At the same time admin users can add and delete products, change order information and so on. We imitated Jingdong Mall to design the website page, so as to improve the user's shopping experience.
## Branch
* develop
## Requirement
* python 3.8.1
* pip install Django==1.11.11
* pip install django-redis==4.11.0
* pip install django-haystack==2.8.1
* pip install elasticsearch==2.4.1
* pip install fdfs-client-py==1.2.6
* pip install Jinja2==2.10.3
* pip install PyMySQL==0.9.3
* pip install redis==4.3.6
* pip install mutagen
* pip install requests
* docker-ce 17.03.2
* sudo docker image pull delron/fastdfs
* sudo docker image pull delron/elasticsearch-ik:2.4.6-1.0
## Instruction
### Check Instruction
* python manage.py
### Run Server
* python manage.py startapp
### Build MySQL Database
* python manage.py makemigrations
* python manage.py migrate
## MySQL Setting
* HOST: 127.0.0.1
* PORT: 3306
* USER: python
* PASSWORD: 123456
* NAME: shoppingmall 

