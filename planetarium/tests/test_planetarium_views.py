from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from planetarium.models import AstronomyShow, PlanetariumDome, ShowSession, ShowTheme
from planetarium.serializers import AstronomyShowListSerializer, AstronomyShowDetailSerializer
from planetarium.tests.test_planetarium import sample_astronomy_show, detail_url

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")


class UnauthenticatedAstronomyShowApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_requires(self):
        res = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAstronomyShowApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_astronomy_shows(self):
        sample_astronomy_show()
        astronomy_show_with_theme = sample_astronomy_show()

        theme = ShowTheme.objects.create(name="TestTheme1")

        astronomy_show_with_theme.show_themes.add(theme)

        res = self.client.get(ASTRONOMY_SHOW_URL)

        astronomy_show = AstronomyShow.objects.all()
        serializer = AstronomyShowListSerializer(astronomy_show, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_astronomy_shows_by_theme(self):
        astronomy_show1 = sample_astronomy_show(title="astronomy show 1")
        astronomy_show2 = sample_astronomy_show(title="astronomy show 2")

        theme1 = ShowTheme.objects.create(name="theme1")
        theme2 = ShowTheme.objects.create(name="theme2")

        astronomy_show1.show_themes.add(theme1)
        astronomy_show2.show_themes.add(theme2)

        astronomy_show3 = sample_astronomy_show(title="Astronomy show without theme")

        res = self.client.get(
            ASTRONOMY_SHOW_URL, {"genres": f"{theme1.id},{theme2.id}"}
        )

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertIn(serializer3.data, res.data)

    def test_filter_movies_by_title(self):
        astronomy_show1 = sample_astronomy_show(title="test show 1")
        astronomy_show2 = sample_astronomy_show(title="test show 2")

        res = self.client.get(
            ASTRONOMY_SHOW_URL, {"title": f"{astronomy_show1.title}"}
        )

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_astronomy_show_detail(self):
        astronomy_show = sample_astronomy_show()
        astronomy_show.show_themes.add(ShowTheme.objects.create(name="TestTheme"))

        url = detail_url(astronomy_show.id)
        res = self.client.get(url)

        serializer = AstronomyShowDetailSerializer(astronomy_show)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_astronomy_show_forbidden(self):
        payload = {
            "title": "Test astronomy show",
            "description": "Astronomy show description",
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminMovieApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com",
            "testpass",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_astronomy_show(self):
        payload = {
            "title": "Test astronomy show",
            "description": "Astronomy show description",
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)

        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(astronomy_show, key))

    def test_create_astronomy_show_with_themes(self):
        theme1 = ShowTheme.objects.create(name="Test theme1")
        theme2 = ShowTheme.objects.create(name="Test theme2")

        payload = {
            "title": "Astronomy show",
            "show_themes": [theme1.id, theme2.id],
            "description": "Test description",
        }
        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])
        show_themes = astronomy_show.show_themes.all()
        self.assertEqual(show_themes.count(), 2)
        self.assertIn(theme1, show_themes)
        self.assertIn(theme2, show_themes)

    def test_delete_and_put_movie_not_allowed(self):
        movie = sample_astronomy_show()
        url = detail_url(movie.id)

        res_del = self.client.delete(url)
        res_put = self.client.put(url)

        self.assertEqual(res_del.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(res_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)