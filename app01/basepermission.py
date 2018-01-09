from tobacco.server import sites


class BasePermission:
    def get_add_btn(self):
        code_list = self.request.permission_code
        if "add" in code_list:
            return True
        else:
            return False

    def get_edit_link(self):
        code_list = self.request.permission_code
        if 'edit' in code_list:
            return super(BasePermission,self).get_edit_link()
        else:
            return []

    def get_list_display(self):
        code_list = self.request.permission_code
        data = []
        if self.list_display:
            data.extend(self.list_display)
            # data.append(TobaccoConfig.edit)
            if 'del' in code_list:
                data.append(sites.TobaccoConfig.delete)
            data.insert(0, sites.TobaccoConfig.check)
        return data