#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.contrib.sessions.models import Session

from mathics.core.definitions import Definitions
from mathics.core.evaluation import Evaluation, Output
from mathics.core.expression import(Expression, Symbol, SymbolTrue, String)
from mathics_django.web.format import format_output


class WebOutput(Output):
    pass

_evaluations = {}


def get_session_evaluation(session):
    evaluation = _evaluations.get(session.session_key)
    if evaluation is None:
        definitions = Definitions(add_builtin=True)
        # We set the formatter to "unformatted" so that we can use
        # our own custom formatter that understand better how to format
        # in the context of mathics-django.
        # Previously, one specific format, like "xml" had to fit all.
        evaluation = Evaluation(
            definitions, format='unformatted', output=WebOutput())
        _evaluations[session.session_key] = evaluation
        evaluation.format_output = lambda expr, format: format_output(evaluation, expr, format)
        Expression('LoadModule', String("pymathics.asy")).evaluate(evaluation)
    return evaluation


def end_session_evaluation(sender, **kwargs):
    session_key = kwargs.get('instance').session_key
    del _evaluations[session_key]

pre_delete.connect(end_session_evaluation, sender=Session)


class Query(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    query = models.TextField()
    result = models.TextField(null=True)
    timeout = models.BooleanField()
    out = models.TextField()
    error = models.BooleanField()

    remote_user = models.CharField(max_length=255, null=True)
    remote_addr = models.TextField(null=True)
    remote_host = models.TextField(null=True)
    browser = models.TextField(null=True)
    meta = models.TextField(null=True)

    log = models.TextField(null=True)


class Worksheet(models.Model):
    user = models.ForeignKey(User,
                             related_name='worksheets',
                             null=True, on_delete=models.CASCADE)

    name = models.CharField(max_length=30)
    content = models.TextField()

    class Meta:
        unique_together = (('user', 'name'),)
