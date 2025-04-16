from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, throttle_classes, permission_classes
from .models import MenuItem
from .serializers import MenuItemSerializer
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage
from rest_framework.views import APIView

# Auth Imports
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group

# Throttling
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

# Create your views here.

@api_view()
def menu_items(request):
    if(request.method=='GET'):
        items = MenuItem.objects.select_related('category').all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)

        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price=to_price)
        if search:
            items = items.filter(title__contains=search)

        if ordering:
            ordering_fields = ordering.split(',')
            for ordering_field in ordering_fields:
                items = items.order_by(ordering_field)

        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []

        serialized_item = MenuItemSerializer(items, many=True)
        return Response(serialized_item.data)
    elif request.method=='POST':
        if request.user.groups.filter(name='Manager').exists():
            serialized_item = MenuItemSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.validated_data, status.HTTP_201_CREATED)
        else:
            return Response({'message':'Access Denied'}, status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({'message':'Access Denied'}, status.HTTP_401_UNAUTHORIZED)

@api_view()
def single_item(request, id):
    item = get_object_or_404(MenuItem, pk=id)
    serialized_item = MenuItemSerializer(item)
    return Response(serialized_item.data, status.HTTP_200_OK)

@api_view()
@permission_classes([IsAuthenticated])
def manager_view(request):
    if request.user.groups.filter(name='Manager').exists():
        return Response({'secret':'message'}, status.HTTP_200_OK)
    else:
        return Response({'secret':'NOT ALLOWED!!!'}, status.HTTP_403_FORBIDDEN)

@api_view()
@permission_classes([IsAuthenticated])
def item_of_the_day(request):
    if request.user.groups.filter(name='Manager').exists():
            serialized_item = MenuItemSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.validated_data, status.HTTP_201_CREATED)
    else:
        return Response({'message':'Access Denied'}, status.HTTP_401_UNAUTHORIZED)


@api_view()
@permission_classes([IsAuthenticated])
def me(request):
    return Response(request.user.email)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def managers(request):
    username = request.data['username']
    if username:
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name='Manager')
        managers.user_set.add(user)
        return Response({'message':'ok'}, status.HTTP_200_OK)
    
    return Response({'message':'error'}, status.HTTP_400_BAD_REQUEST)
    
@api_view()
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def throttle_check(request):
    return Response({'message':'successful'})