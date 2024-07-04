from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from config.settings import PAGINATE_COUNT
from movies.models import Filmwork


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        return Filmwork.objects.prefetch_related(
            'genres', 'person'
        ).values().all().annotate(
            genres=ArrayAgg('genres__name', distinct=True),
            actors=ArrayAgg(
                'persons__full_name', filter=Q(
                    personfilmwork__role='actor'
                ), distinct=True
            ),
            directors=ArrayAgg(
                'persons__full_name', filter=Q(
                    personfilmwork__role='director'
                ), distinct=True
            ),
            writers=ArrayAgg(
                'persons__full_name', filter=Q(
                    personfilmwork__role='writer'
                ), distinct=True
            )
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = PAGINATE_COUNT

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset,
            self.paginate_by
        )
        page_num = self.request.GET.get('page', 1)
        if page_num == 'last':
            page_num = paginator.num_pages
        results = paginator.page(page_num)
        return {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': (
                results.previous_page_number()
                if results.has_previous() else None
            ),
            'next': results.next_page_number() if results.has_next() else None,
            'results': list(results.object_list)
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs):
        return {**kwargs['object']}
