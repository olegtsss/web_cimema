from django.contrib import admin

from .models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'description', 'created', 'modified'
    )
    list_filter = ('name',)
    search_fields = ('name', 'created', 'id')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'created', 'modified'
    )
    list_filter = ('full_name',)
    search_fields = ('full_name', 'id')


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmworkInline, PersonFilmworkInline)
    list_display = (
        'title', 'type', 'creation_date', 'rating', 'created', 'modified'
    )
    list_filter = ('type',)
    search_fields = ('title', 'description', 'id')
