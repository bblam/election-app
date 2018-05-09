from django.contrib.auth import authenticate, login, logout

from rest_framework import viewsets
from rest_framework import generics
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from election.models import Party, User, Vote
from election.serializers import PartySerializer, UserSerializer
from election.serializers import AppointSerializer, VoteAllSerializer
from election.serializers import LoginSerializer, VoteSerializer
from election.serializers import CastVoteSerializer, UnvoteSerializer
from election.serializers import ResultSerializer


class PartyViewSet(viewsets.ModelViewSet):
    """
    This view automatically provides 'list', 'create', 'retrieve',
    'update' and 'destroy' actions.
    """
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request):
        req = request.data
        ret = {'error': 'Please provide party name'}
        if req['name']:
            name = req['name']
            detail = req['detail']
            party = Party(name=name, detail=detail)
            party.save()
            ret = {'success': request.data}
        return Response(ret)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        req = request.data
        user = User.objects.create_user(username=req['username'],
                                        password=req['password'],
                                        firstname=req['firstname'],
                                        lastname=req['lastname'])
        user.save()
        return Response(request.data)


class LoginView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = LoginSerializer

    def create(self, request):
        print(request.data['username'])
        print(request.data['password'])
        user = authenticate(username=request.data['username'],
                            password=request.data['password'])
        print(user)
        ret = {'success': 0}

        if user is not None:
            if user.is_active:
                login(request, user)
                ret = {'return': request.data, 'success': 1,
                       'session': request.session.session_key}
        return Response(ret)


class LogoutView(generics.ListAPIView):

    def get(self, request, format=None):
        logout(request)
        return Response("Logout")


class AppointViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AppointSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          permissions.IsAdminUser,)

    def update(self, request, pk=None):
        obj = self.get_object()
        req = request.data
        ret = {'return': 'That position is already taken.'}
        position = User.objects.all().filter(party=req['party'],
                                             position=req['position']).exclude(
            party=Party.objects.get(name='Independent'))

        if not position:
            obj.position = req['position']
            obj.party = Party.objects.get(id=req['party'])
            obj.save(update_fields=['position', 'party'])
            serializer = AppointSerializer(obj)
            ret = {'return': serializer.data}
        return Response(ret)


class VoteViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().exclude(position=0)
    serializer_class = VoteSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request):
        req = request.data
        user = User.objects.get(username=request.user)
        candidate = User.objects.get(username=req['username'])
        ret = {'return': "You can't vote for yourself"}
        if request.user != candidate:
            candidate2 = User.objects.filter(position=candidate.position).\
                first()
            voted = Vote.objects.filter(user=request.user,
                                        candidate=candidate2)

            ret = {'return': "You've already voted for this position"}
            if not voted:
                vote = Vote(user=user, candidate=candidate)
                vote.save()
                ret = {'return': 'Successfully voted for candidate'}
        return Response(ret)


class VoteAllViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = VoteAllSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request):
        req = request.data
        party = Party.objects.get(name=req['name'])
        candidate_set = User.objects.filter(party=party)

        ret = {'return': 'No available candidates for this party.'}
        if candidate_set:
            ret = {'return': "You've voted for the candidates"
                             "of this party."}
            for candidate in candidate_set:
                voted = Vote.objects.filter(user=request.user,
                                            candidate=candidate)
                if not voted:
                    print('u: ', request.user, ' c: ', candidate.username)
                    vote = Vote(user=request.user, candidate=candidate)
                    vote.save()
        return Response(ret)


class CastVoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = CastVoteSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def list(self, request, *args, **kwargs):
        vote = Vote.objects.filter(user=request.user)
        serializer = CastVoteSerializer(vote, many=True)
        return Response(serializer.data)

    def create(self, request):
        candidate_set = Vote.objects.filter(user=request.user)

        ret = {'return': "You didn't vote for any candidate."}
        if candidate_set:
            ret = {'return': "Votes Finalized"}
            for candidate in candidate_set:
                candidate.flag = 1
                candidate.save()
        return Response(ret)


class UnvoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = UnvoteSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def list(self, request, *args, **kwargs):
        vote = Vote.objects.filter(user=request.user)
        serializer = UnvoteSerializer(vote, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        vote = self.get_object()
        ret = {'return': "You can't unvote this candidate."}
        if vote.flag == 0:
            ret = {'return': "Successfully unvoted candidate"}
            self.perform_destroy(vote)
        return Response(ret)


class ResultView(generics.ListAPIView):
    queryset = User.objects.exclude(position=0)
    serializer_class = ResultSerializer