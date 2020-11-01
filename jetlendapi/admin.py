from django.contrib import admin

from jetlendapi import models


class IdentifierImageAdmin(admin.StackedInline):
    model = models.PassportImage

class CvalsImageAdmin(admin.StackedInline):
    model = models.CvalificationImage

class AgreementAdmin(admin.StackedInline):
    model = models.PolicyAgreement

@admin.register(models.CvalificationImage)
class CvalsImageAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PolicyAgreement)
class AgreementAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Identifier)
class IdentifierAdmin(admin.ModelAdmin):
    inlines = [IdentifierImageAdmin]

    class Meta:
        model = models.Identifier


@admin.register(models.PassportImage)
class IdentifierImageAdmin(admin.ModelAdmin):
    pass

@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('date_of_creation',)