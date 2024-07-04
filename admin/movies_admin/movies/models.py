import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from config.settings import CHAR_FIELD_MAX_LENGTH, RATING_MAX, RATING_MIN

TYPE = [
    ('movie', _('movie')),
    ('tv_show', _('tv_show')),
]


class Gender(models.TextChoices):
    MALE = 'male', _('male')
    FEMALE = 'female', _('female')


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(
        _('name'), unique=True, max_length=CHAR_FIELD_MAX_LENGTH
    )
    description = models.TextField(_('description'), null=True, blank=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('genre')
        verbose_name_plural = _('genries')


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(
        _('name'), max_length=CHAR_FIELD_MAX_LENGTH, null=True
    )
    gender = models.TextField(_('gender'), choices=Gender.choices, null=True)

    def __str__(self):
        return str(self.full_name)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('actor')
        verbose_name_plural = _('actors')


class PersonFilmwork(UUIDMixin):
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    role = models.CharField(
        _('role'), max_length=CHAR_FIELD_MAX_LENGTH, null=True
    )
    created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        unique_together = ('film_work', 'person', 'role')


class Filmwork(UUIDMixin, TimeStampedMixin):
    file_path = models.FileField(
        _('file'), blank=True, null=True, upload_to='movies/'
    )
    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField(Person, through='PersonFilmwork')
    title = models.CharField(
        _('title'), max_length=CHAR_FIELD_MAX_LENGTH, null=True,)
    description = models.TextField(
        _('description'), blank=True, null=True
    )
    creation_date = models.DateField(_('created'), blank=True, null=True,)
    rating = models.FloatField(
        _('rating'), blank=True, null=True,
        validators=[
            MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)
        ]
    )
    type = models.CharField(
        _('type'), choices=TYPE, default=TYPE[0],
        max_length=CHAR_FIELD_MAX_LENGTH,
    )

    def __str__(self):
        return str(self.title)

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('film')
        verbose_name_plural = _('films')


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
    created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        unique_together = ('film_work', 'genre')
