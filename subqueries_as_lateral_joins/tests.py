import pytest
from django.db.models import OuterRef

from .models import Comment, JoinSubquery, Post

pytestmark = pytest.mark.django_db


def test_annotate_subquery_as_join():
    article_1 = Post.objects.create(title="Article 1")
    Comment.objects.create(post=article_1, email="joe@asdf.com")
    Comment.objects.create(post=article_1, email="bob@asdf.com")
    article_2 = Post.objects.create(title="Article 2")
    Comment.objects.create(post=article_2, email="frank@hjkl.com")
    Comment.objects.create(post=article_2, email="steve@hjkl.com")

    newest = Comment.objects.filter(post=OuterRef("pk")).order_by("-created_at")
    queryset = Post.objects.annotate(
        newest_commenter_email=JoinSubquery(newest.values("email")[:1])
    )

    assert list(queryset.values("title", "newest_commenter_email")) == [
        {"title": "Article 1", "newest_commenter_email": "bob@asdf.com"},
        {"title": "Article 2", "newest_commenter_email": "steve@hjkl.com"},
    ]
