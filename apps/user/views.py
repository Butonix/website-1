import json

from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import Http404, HttpResponse,JsonResponse
from django.shortcuts import render, redirect,reverse

# Create your views here.

from django.contrib.auth.views import method_decorator,login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.base import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from apps.article.models import Article_add, Category_Article
from apps.article.serializers import ArticleSerializer
from apps.article.views import StandardResultsSetPagination
from apps.uitls.permissions import IsOwnerOrReadOnly
from apps.user.filter import CategoryFilter, UserFilter
from apps.user.models import User, Follow
from apps.user.serializers import UserSerializer
from .forms import CaptchaTestForm, LoginForms, Follow_Forms
from rest_framework import viewsets, mixins, status, permissions
from rest_framework.pagination import PageNumberPagination

def test(request):
    form = CaptchaTestForm()
    return render(request,'test.html',{'form':form})

def captcha_refresh(request):
    print('=========')
    """  Return json with new captcha for ajax refresh request """
    if not request.is_ajax():
 # 只接受ajax提交
        raise Http404
    new_key = CaptchaStore.generate_key()
    to_json_response = {
        'key': new_key,
        'image_url': captcha_image_url(new_key),
    }
    print(to_json_response)
    return HttpResponse(json.dumps(to_json_response), content_type='application/json')

def yan(request):
    cs = CaptchaStore.objects.filter(response=request.POST['response'], hashkey=request.POST['hashkey'])
    if cs:
        return JsonResponse({"success":"ok"})
    else:
        return JsonResponse({'error':'shibai'})




    #===============

class CustomBackend(ModelBackend):
    """进行手机登录验证"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(Q(mobile=username) | Q(username=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


def login_view(request):
    if request.method == 'GET':
        return render(request,'pc/logoin.html')
    if request.method == 'POST':
        form = LoginForms(request.POST)
        if form.is_valid():
            telephone = form.cleaned_data.get('telephone')
            password = form.cleaned_data.get('password')
            remember = form.cleaned_data.get('remember')
            user = authenticate(request,username=telephone,password=password)
            if user:
                if user.is_active:
                    login(request,user)
                    if remember:
                        request.session.set_expiry(None)
                    else:
                        request.session.set_expiry(0)
                    return JsonResponse({"code":200,"message":"","data":{}})
                    #return restful.result()
                else:
                    return JsonResponse({"code": 401, "message": "此账号暂无权限，请联系管理员", "data": {}})
                    #return restful.unauth(message='此账号暂无权限，请联系管理员')
            else:
                return JsonResponse({"code": 400, "message": "手机号码或者密码错误", "data": {}})
                #return restful.params_error(message="手机号码或者密码错误")
        else:
            errors = form.get_errors()
            return JsonResponse({"code":400,"message":"","data":errors})
            #return restful.params_error(message=errors)

def logout_view(request):
    logout(request)
    return redirect('/index')


class Author(View):
    def get(self,request):
        return
    @method_decorator(login_required(login_url='/login'))
    def post(self,request):
        if request.user is not None and  request.user.is_authenticated:
            froms = Follow_Forms(request.POST)
            if froms.is_valid():
                follow = Follow()
                if request.POST.get('follow') == str(request.user.id):
                    return JsonResponse({'status': 201, 'message': '不能自己关注自己'})
                else:
                    cun = Follow.objects.filter(follow=froms.cleaned_data.get('follow'),fan=request.user.id)
                    if cun:
                        cun.delete()
                        return JsonResponse({'status': 200, 'message': '已取消关注'})
                    follow.follow = froms.cleaned_data.get('follow')
                    follow.fan_id = request.user.id
                    follow.save()
                    return JsonResponse({'status':200,'message':'成功关注'})
            else:
                return JsonResponse({'status':400,'message':'失败'})
        return JsonResponse({"status":302,"message":"未登录"})


"""个人中心"""
@method_decorator(login_required(login_url='/login'),name='dispatch')
class Person(View):

    @method_decorator(login_required(login_url='/login'),name='dispatch')
    def get(self,request):

        category = Category_Article.objects.all()
        count = User.objects.filter(follow__fan__id=request.user.id).count()
        floow = User.objects.filter(fan__follow_id=request.user.id).count()

        return render(request,'pc/person/index.html',{'category':category,'count':count,'floow':floow})


class PersonDetaile(View):

    def get(self,request,article_id):
        category = Category_Article.objects.all()
        count = User.objects.filter(follow__fan__id=article_id).count()
        floow = User.objects.filter(follow__fan__id=article_id).count()
        user = User.objects.get(id=article_id)

        if article_id ==request.user.id:
            return redirect(reverse('user:person'))
        return render(request,'pc/person/index1.html',{'category':category,'count':count,'floow':floow,'user':user})


class PersonApi(viewsets.ReadOnlyModelViewSet):
    """
    个人中心
    """
    queryset = Article_add.objects.filter(is_show=True)
    serializer_class = ArticleSerializer
    permission_classes = (IsAuthenticated,IsOwnerOrReadOnly)#未登录禁止访问
    filter_backends = (DjangoFilterBackend,)
    filter_class = CategoryFilter
    authentication_classes = (SessionAuthentication,)
    pagination_class = StandardResultsSetPagination
    # def list(self, request, *args, **kwargs):
    #         queryset =  Article_add.objects.filter(authors_id=self.request.user.id).order_by('-add_time')
    #         serializer = ArticleSerializer(queryset, many=True)
    #
    #         page = self.paginate_queryset(queryset)
    #         if page is not None:
    #             serializer = self.get_serializer(page, many=True)
    #             return self.get_paginated_response(serializer.data)
    #         return Response(serializer.data)
    # def get_queryset(self):
    #     return Article_add.objects.filter(authors_id=self.request.user.id)

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        user = self.request.user
        #User.objects.filter()

        user_id = self.request.query_params.get('pk')
        if user_id:
            return Article_add.objects.filter(authors_id=user_id).filter(is_show=True).order_by('-add_time')
        else:
            return Article_add.objects.filter(authors_id=self.request.user.id).filter(is_show=True).order_by(
                '-add_time')


# class PersonOthers(viewsets.ReadOnlyModelViewSet):
#     """
#     他个人中心 (未用)
#     """
#     queryset = Article_add.objects.filter(is_show=True)
#     serializer_class = ArticleSerializer
#     permission_classes = (IsAuthenticated,IsOwnerOrReadOnly)#未登录禁止访问
#     filter_backends = (DjangoFilterBackend,)
#     filter_class = CategoryFilter
#     authentication_classes = (SessionAuthentication,)
#     def get_queryset(self):
#         print(self.request.query_params.get('pk'))
#         try:
#             #print(self.kwargs['pk'])
#             #user_id = self.kwargs['pk']
#             user_id = self.request.query_params.get('pk')
#             if user_id:
#                 print(Article_add.objects.filter(authors_id=user_id).filter(is_show=True).order_by('-add_time'))
#                 return Article_add.objects.filter(authors_id=user_id).filter(is_show=True).order_by('-add_time')
#         except Exception:
#             pass



    #print()
    # queryset = User.objects.all()
    # serializer_class = UserSerializer
    # permission_classes = (IsAuthenticated,IsOwnerOrReadOnly)#未登录禁止访问
    # filter_backends = (DjangoFilterBackend,filters.SearchFilter)
    # filter_class = UserFilter
    # search_fields = ('mobile',)
    # authentication_classes = (SessionAuthentication,)
    # def get_queryset(self):
    #     print(self.request.query_params.get('article_id'))

class UserGetAllInfo(mixins.ListModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)  # 未登录禁止访问
    authentication_classes = [SessionAuthentication, JSONWebTokenAuthentication]


class UserGetInfo(UserGetAllInfo):
    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.id)


class UserDisbale(mixins.ListModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)  # 未登录禁止访问
    authentication_classes = [SessionAuthentication, JSONWebTokenAuthentication]

    pass