from rest_framework import serializers

# Blog app serializers
class BlogCategorySerializer(serializers.Serializer): pass
class BlogTagSerializer(serializers.Serializer): pass
class BlogPostSerializer(serializers.Serializer): pass
class BlogPostDetailSerializer(serializers.Serializer): pass
class BlogCommentSerializer(serializers.Serializer): pass
class BlogCommentCreateSerializer(serializers.Serializer): pass
class BlogLikeSerializer(serializers.Serializer): pass
class BlogViewSerializer(serializers.Serializer): pass
class BlogSeriesSerializer(serializers.Serializer): pass
class PublicBlogCategorySerializer(serializers.Serializer): pass
class PublicBlogTagSerializer(serializers.Serializer): pass
class PublicBlogPostSerializer(serializers.Serializer): pass
class PublicBlogCommentSerializer(serializers.Serializer): pass
