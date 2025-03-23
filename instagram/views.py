import json
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Post, Follow
from .serializers import UserSerializer

# 회원가입
@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': '회원가입이 완료되었습니다!'}, status=201)
    return Response({'오류': '회원가입에 실패하였습니다.', '상세': serializer.errors}, status=400)


# 로그인 API (jwt 발급)
@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'message': '로그인 성공!'
        })
    return Response({'오류': '로그인 실패. 아이디 또는 비밀번호를 확인하세요.'}, status=401)


# jwt 토큰 갱신 API
@api_view(['POST'])
def refresh_token(request):
    refresh = request.data.get('refresh_token')

    if not refresh:
        return Response({'오류': '리프레시 토큰이 필요합니다.'}, status=400)

    try:
        new_access_token = RefreshToken(refresh).access_token
        return Response({'access_token': str(new_access_token), 'message': '토큰 갱신 성공!'})
    except Exception:
        return Response({'오류': '유효하지 않은 토큰입니다.'}, status=400)


# 게시글 생성 API
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_post(request):
    try:
        data = request.data
        image = request.FILES.get('image')
        post = Post.objects.create(
            user=request.user,
            title=data['title'],
            contents=data['contents'],
            image=image
        )
        return Response({
            "id": post.id,
            "title": post.title,
            "contents": post.contents,
            "image_url": post.image.url if post.image else None,
            "message": "게시글이 성공적으로 등록되었습니다!"}, status=201)
    except KeyError:
        return Response({"오류": "필수 항목이 누락되었습니다. 제목과 내용을 입력하세요."}, status=400)


# 게시글 조회 API
@api_view(['GET'])
def get_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        return Response({"id": post.id, "title": post.title, "contents": post.contents})
    except Post.DoesNotExist:
        return Response({"오류": "해당 게시글을 찾을 수 없습니다."}, status=404)


# 팔로우 API
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def follow(request):
    try:
        data = request.data
        followee = User.objects.get(id=data['followee_id'])
        follow = Follow.objects.create(follower=request.user, followee=followee)
        return Response({"follower_id": follow.follower.id, "followee_id": follow.followee.id, "message": "팔로우 성공!"}, status=201)

    except (KeyError, User.DoesNotExist):
        return Response({"오류": "팔로우할 사용자를 찾을 수 없습니다."}, status=400)


# 특정 사용자의 팔로우 리스트 조회 API
@api_view(['GET'])
def follow_list(request, user_id):
    follows = Follow.objects.filter(follower_id=user_id).values("followee_id")
    return Response({"followees": list(follows), "message": "팔로우 목록을 가져왔습니다!"})


# 뉴스피드 API (팔로우한 사용자의 게시글 최신순 정렬)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def newsfeed(request):
    user = request.user  # JWT 인증된 사용자
    following_users = Follow.objects.filter(follower=user).values_list('followee', flat=True)  # 팔로우한 사람들 ID 가져오기

    # 해당 사용자의 팔로우한 사람들의 게시글을 최신순으로 가져오기
    posts = Post.objects.filter(user_id__in=following_users) \
        .select_related('user') \
        .prefetch_related('comments') \
        .order_by('-created_at')

    # 결과 반환
    post_list = [
        {
            "id": post.id,
            "user_id": post.user.id,
            "username": post.user.username,
            "title": post.title,
            "contents": post.contents,
            "created_at": post.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for post in posts
    ]

    return Response({"newsfeed": post_list, "message": "뉴스피드를 가져왔습니다!"}, status=200)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_post(request):
    user = request.user
    title = request.data.get('title')
    contents = request.data.get('contents')
    image = request.FILES.get('image')  # 이미지 파일은 FILES에서 가져와야 함

    post = Post.objects.create(
        user=user,
        title=title,
        contents=contents,
        image=image
    )

    return Response({
        'message': '게시글이 업로드되었습니다!',
        'post': {
            'id': post.id,
            'title': post.title,
            'contents': post.contents,
            'image_url': post.image.url if post.image else None,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })