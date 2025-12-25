from rest_framework import serializers

# Serializers for programs app
class ProgramCategorySerializer(serializers.Serializer): pass
class ProgramSerializer(serializers.Serializer): pass
class ProgramDetailSerializer(serializers.Serializer): pass
class ProgramApplicationSerializer(serializers.Serializer): pass
class ProgramApplicationCreateSerializer(serializers.Serializer): pass
class ProgramUpdateSerializer(serializers.Serializer): pass
class ProgramResourceSerializer(serializers.Serializer): pass
class ProgramParticipantSerializer(serializers.Serializer): pass
class ProgramEventSerializer(serializers.Serializer): pass
class PublicProgramSerializer(serializers.Serializer): pass
class PublicProgramCategorySerializer(serializers.Serializer): pass

# Additional serializers that might be needed
class ProgramStatsSerializer(serializers.Serializer): pass
