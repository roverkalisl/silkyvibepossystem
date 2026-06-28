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
            "barcode",
            "name",
            "description",
            "category",
            "brand",
            "size",
            "color",
            "image",
            "stock_quantity",
            "reserved_quantity",
            "damaged_quantity",
            "returned_quantity",
            "min_stock_level",
            "cost_price",
            "price",
            "discount_price",
            "is_on_sale",
            "sale_start_date",
            "sale_end_date",
        ]
        widgets = {
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "SKU"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Barcode"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Product name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control", "placeholder": "Brand"}),
            "size": forms.TextInput(attrs={"class": "form-control", "placeholder": "Size"}),
            "color": forms.TextInput(attrs={"class": "form-control", "placeholder": "Color"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "reserved_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "damaged_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "returned_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "min_stock_level": forms.NumberInput(attrs={"class": "form-control"}),
            "cost_price": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "discount_price": forms.NumberInput(attrs={"class": "form-control"}),
            "sale_start_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "sale_end_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }
