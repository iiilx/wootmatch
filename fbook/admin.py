from django.contrib import admin
from fbook.models import * 

class ClientAdmin(admin.ModelAdmin):
    pass

class SuggestionAdmin(admin.ModelAdmin):
    pass

class FbookUserAdmin(admin.ModelAdmin):
    pass

class LikeAdmin(admin.ModelAdmin):
    pass

class VoteAdmin(admin.ModelAdmin):
    pass

class MatchStatAdmin(admin.ModelAdmin):
    pass

admin.site.register(MatchStat,MatchStatAdmin)
admin.site.register(Vote,VoteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
admin.site.register(FbookUser,FbookUserAdmin)
admin.site.register(Like,LikeAdmin)
admin.site.register(Client, ClientAdmin)

