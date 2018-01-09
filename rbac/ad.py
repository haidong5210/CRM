from tobacco.server import sites
from rbac import models


class UserConfig(sites.TobaccoConfig):
    list_display = ['username','email']
    edit_link = ['username']

sites.site.register(models.User,UserConfig)


class RoleConfig(sites.TobaccoConfig):
    list_display = ['title']
    edit_link = ['title']

sites.site.register(models.Role,RoleConfig)


class GroupConfig(sites.TobaccoConfig):
    list_display = ['name']
    edit_link = ['name']
sites.site.register(models.Group,GroupConfig)


class PermissionConfig(sites.TobaccoConfig):
    list_display = ['title']
    edit_link = ['title']
sites.site.register(models.Permission,PermissionConfig)


class MenueConfig(sites.TobaccoConfig):
    list_display = ['title']
    edit_link = ['title']
sites.site.register(models.Menue,PermissionConfig)