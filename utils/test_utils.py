# -*- coding: utf-8 -*-

def set_fake_deepcopy(cls):
    def fake_copy(self, memo):
        return self
    setattr(cls, '__deepcopy__', fake_copy)
