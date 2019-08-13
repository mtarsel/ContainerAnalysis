FROM python:3.7
COPY get-image-info.py CAP/get-image-info.py
COPY docs/test_user.yaml CAP/test_user.yaml
COPY objects CAP/objects
COPY utils CAP/utils
COPY requirements.txt CAP/requirements.txt
WORKDIR CAP
RUN ls -a
RUN pip install -r requirements.txt
CMD python get-image-info.py test_user.yaml
