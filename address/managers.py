from django.db import models


class CountryManager(models.Manager):
    def get_queryset(self):
        return super(CountryManager, self).get_queryset()
    def active(self):
        return self.filter(is_active=True)
    def get_country(self, id):
        if self.filter(id=id).exists():
            return self.get(id=id)
        return None
    def get_in(self):
        try:
            return self.get(code="IN")
        except:
            None


class StateManager(models.Manager):
    def get_queryset(self):
        return super(StateManager, self).get_queryset()
    def active(self):
        return self.filter(is_active=True)
    def get_state(self, id):
        if self.filter(id=id).exists():
            return self.get(id=id)
        return None
