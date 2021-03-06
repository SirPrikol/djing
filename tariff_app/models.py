from datetime import datetime
from django.db import models, IntegrityError
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from .base_intr import TariffBase, PeriodicPayCalcBase
from .custom_tariffs import TARIFF_CHOICES, PERIODIC_PAY_CHOICES
from group_app.models import Group
from djing.lib import MyChoicesAdapter
from jsonfield import JSONField


class TariffManager(models.Manager):
    def get_tariffs_by_group(self, group_id):
        return self.filter(groups__id__in=(group_id,))


class Tariff(models.Model):
    title = models.CharField(_('Service title'), max_length=32)
    descr = models.CharField(_('Service description'), max_length=256)
    speedIn = models.FloatField(_('Speed In'), default=0.0)
    speedOut = models.FloatField(_('Speed Out'), default=0.0)
    amount = models.FloatField(_('Price'), default=0.0)
    calc_type = models.CharField(_('Script'), max_length=2, default=TARIFF_CHOICES[0][0],
                                 choices=MyChoicesAdapter(TARIFF_CHOICES))
    is_admin = models.BooleanField(_('Tech service'), default=False)

    groups = models.ManyToManyField(Group, blank=True)

    objects = TariffManager()

    def get_calc_type(self):
        """
        :return: Child of tariff_app.base_intr.TariffBase,
                 methods which provide the desired logic of payments
        """
        calc_code = self.calc_type
        for choice_pair in TARIFF_CHOICES:
            choice_code, logic_class = choice_pair
            if choice_code == calc_code:
                if not issubclass(logic_class, TariffBase):
                    raise TypeError
                return logic_class

    def calc_deadline(self):
        calc_type = self.get_calc_type()
        calc_obj = calc_type(self)
        return calc_obj.calc_deadline()

    def __str__(self):
        return "%s (%.2f)" % (self.title, self.amount)

    class Meta:
        db_table = 'tariffs'
        ordering = ('title',)
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        unique_together = ('speedIn', 'speedOut', 'amount', 'calc_type')


class PeriodicPay(models.Model):
    name = models.CharField(_('Periodic pay name'), max_length=64)
    when_add = models.DateTimeField(_('When pay created'), auto_now_add=True)
    calc_type = models.CharField(_('Script type for calculations'), max_length=2, default='df',
                                 choices=MyChoicesAdapter(PERIODIC_PAY_CHOICES))
    amount = models.FloatField(_('Total amount'))
    extra_info = JSONField()

    def _get_calc_object(self):
        """
        :return: subclass of custom_tariffs.PeriodicPayCalcBase with required
        logic depending on the selected in database.
        """
        calc_code = self.calc_type
        for choice_pair in PERIODIC_PAY_CHOICES:
            choice_code, logic_class = choice_pair
            if choice_code == calc_code:
                if not issubclass(logic_class, PeriodicPayCalcBase):
                    raise TypeError
                return logic_class()

    def get_next_time_to_pay(self, last_time_payment):
        #
        # last_time_payment may be None if it is a first payment
        #
        calc_obj = self._get_calc_object()
        res = calc_obj.get_next_time_to_pay(self, last_time_payment)
        if type(res) is not datetime:
            raise TypeError
        return res

    def calc_amount(self):
        calc_obj = self._get_calc_object()
        res = calc_obj.calc_amount(self)
        if type(res) is not float:
            raise TypeError
        return res

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'periodic_pay'
        verbose_name = _('Periodic pay')
        verbose_name_plural = _('Periodic pays')
        ordering = ('-id',)


@receiver(models.signals.pre_delete, sender=PeriodicPay)
def periodic_pay_pre_delete(sender, **kwargs):
    raise IntegrityError('All linked abonapp.PeriodicPayForId will be removed, be careful')
