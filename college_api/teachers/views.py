from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Teacher
from .serializers import TeacherSerializer

@api_view(['GET', 'POST'])
def teacher_list(request):
    
    if request.method == 'GET':
        teachers = Teacher.objects.all()
        serializer = TeacherSerializer(teachers, many=True)
        
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TeacherSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)