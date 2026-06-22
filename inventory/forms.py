from django import forms

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "category-slug"}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "sku",
            "name",
            "description",
            "category",
            "image",
            "stock_quantity",
            "price",
            "discount_price",
            "is_on_sale",
            "sale_start_date",
            "sale_end_date",
        ]
        widgets = {
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "SKU"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Product name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "discount_price": forms.NumberInput(attrs={"class": "form-control"}),
            "sale_start_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "sale_end_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }
