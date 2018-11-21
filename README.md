# VEH

VEH stands for **V**ienna **E**ntity **H**ub and is a web application/service for entities mentioned in texts written in the time of Arthur Schnitzler.
VEH is based upon [djangobaseproject](https://github.com/acdh-oeaw/djangobaseproject) and [apis-core](https://github.com/acdh-oeaw/apis-core).

# Install

1. clone the repo
2. create a virtual env
3. install requirements
4. In `veh.urls.py` comment `url(r'^apis/', include('apis_core.urls', namespace="apis")),` out.
5. Run `manage.py migrate`
6. Uncomment `url(r'^apis/', include('apis_core.urls', namespace="apis")),`

and you should be good to go (`manage.py runserver`)
