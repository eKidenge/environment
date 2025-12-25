from rest_framework import serializers

# Core app serializers
class SiteConfigurationSerializer(serializers.Serializer): pass
class TeamMemberSerializer(serializers.Serializer): pass
class PartnerOrganizationSerializer(serializers.Serializer): pass
class ImpactMetricSerializer(serializers.Serializer): pass
class FAQSerializer(serializers.Serializer): pass
class SitePageSerializer(serializers.Serializer): pass
class NewsletterSubscriptionSerializer(serializers.Serializer): pass
class PublicSiteConfigurationSerializer(serializers.Serializer): pass
class PublicTeamMemberSerializer(serializers.Serializer): pass
class PublicPartnerOrganizationSerializer(serializers.Serializer): pass
class PublicImpactMetricSerializer(serializers.Serializer): pass
class PublicFAQSerializer(serializers.Serializer): pass
class PublicSitePageSerializer(serializers.Serializer): pass
class NewsletterSubscriptionCreateSerializer(serializers.Serializer): pass
