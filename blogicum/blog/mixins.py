from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View

from .models import Comment, Post


class PostMixin:
    model = Post
    POSTS_PER_PAGE = 10
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        return (
            self.model.objects.select_related(
                'location', 'author', 'category'
            )
            .filter(is_published=True,
                    category__is_published=True,
                    pub_date__lte=timezone.now())
            .annotate(comment_count=Count("comment"))
            .order_by("-pub_date"))


class DispatchNeededMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail', id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


class CommentMixin(View):
    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(
            self.model,
            pk=kwargs['comment_id'],
        )
        if comment.author != request.user:
            return redirect('blog:post_detail', id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "blog:post_detail", kwargs={'id': self.kwargs['post_id']}
        )
