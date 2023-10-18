from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post, User
from .utils import get_post_data
from blog.mixins import CommentMixin, DispatchNeededMixin, PostMixin

POSTS_PER_PAGE = 10


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:profile", args=[self.request.user])


class PostUpdateView(
    LoginRequiredMixin, DispatchNeededMixin, PostMixin, UpdateView
):
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'id': self.kwargs['post_id']}
        )


class PostDeleteView(
    LoginRequiredMixin, DispatchNeededMixin, PostMixin, DeleteView
):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse(
            "blog:profile", kwargs={"username": self.request.user}
        )


class IndexListView(PostMixin, ListView):
    template_name = 'blog/index.html'


class ProfileListView(ListView):
    model = Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/profile.html'
    user = None

    def get_queryset(self):
        user = get_object_or_404(
            User, username=self.kwargs['username']
        )
        if self.request.user == user:
            return (
                self.model.objects.select_related('author')
                .filter(author=user)
                .annotate(comment_count=Count("comment"))
                .order_by("-pub_date")
            )
        else:
            return (
                self.model.objects.select_related('author')
                .filter(
                    Q(is_published=True) & Q(
                        pub_date__lte=timezone.now()
                    ) & Q(author=user)
                )
                .annotate(comment_count=Count("comment"))
                .order_by("-pub_date")
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    form_class = ProfileEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("blog:profile", args=[self.request.user])


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Post, pk=self.kwargs['id'])
        if obj.author == self.request.user or (
            obj.is_published and obj.pub_date <= timezone.now()
        ):
            return obj
        else:
            raise Http404("Post does not exist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comment.select_related('author')
        return context


class CategoryPostsListView(PostMixin, ListView):
    template_name = 'blog/category.html'

    def get_queryset(self):
        category = get_object_or_404(
            Category, 
            slug=self.kwargs['category_slug'], 
            is_published=True
        )
        queryset = super().get_queryset().filter(category=category,)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category.objects.values(
                'id', 'title', 'description'
            ), slug=self.kwargs['category_slug']
        )
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    post_obj = None

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_post_data(kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "blog:post_detail", kwargs={'id': self.kwargs['post_id']}
        )


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    pass

