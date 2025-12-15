"""
Report views for OKR Performance System
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Q
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal
from .models import (
    MonthlyEvaluation, PeerEvaluation, MonthlyReport, 
    DepartmentReport, WorkHours, PerformanceScore, AdminEvaluationHistory
)
from .serializers import (
    MonthlyEvaluationSerializer, SelfEvaluationCreateSerializer,
    PeerEvaluationSerializer, PeerEvaluationCreateSerializer,
    AdminFinalEvaluationSerializer, MonthlyEvaluationSummarySerializer,
    WorkHoursSerializer, WorkHoursCreateSerializer, AdminEvaluationHistorySerializer
)

User = get_user_model()


class MonthlyEvaluationViewSet(viewsets.ModelViewSet):
    """月度综合评价视图集"""
    serializer_class = MonthlyEvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = MonthlyEvaluation.objects.all()
        
        # 过滤参数
        month = self.request.query_params.get('month')
        user_id = self.request.query_params.get('user')
        
        if month:
            queryset = queryset.filter(month=month)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 非管理员只能查看自己的评价
        if self.request.user.role != 'admin':
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user', 'admin_evaluated_by').prefetch_related('peer_evaluations').order_by('-month', 'user__name')
    
    @swagger_auto_schema(
        method='post',
        operation_description="提交自我评价",
        request_body=SelfEvaluationCreateSerializer,
        responses={
            201: MonthlyEvaluationSerializer,
            400: "验证错误"
        }
    )
    @action(detail=False, methods=['post'], url_path='self-evaluation')
    def submit_self_evaluation(self, request):
        """提交自我评价"""
        serializer = SelfEvaluationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            with transaction.atomic():
                # 检查是否已存在，如果存在则更新
                existing_evaluation = MonthlyEvaluation.objects.filter(
                    user=request.user,
                    month=serializer.validated_data['month']
                ).first()
                
                if existing_evaluation:
                    # 更新现有评价
                    for key, value in serializer.validated_data.items():
                        if key != 'month':  # 不更新月份
                            setattr(existing_evaluation, key, value)
                    existing_evaluation.save()
                    evaluation = existing_evaluation
                else:
                    # 创建新评价
                    evaluation = serializer.save()
                
                return Response(
                    MonthlyEvaluationSerializer(evaluation, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='post',
        operation_description="提交他人评价",
        request_body=PeerEvaluationCreateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="评价月份 (YYYY-MM-DD格式)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=True
            )
        ],
        responses={
            201: PeerEvaluationSerializer,
            400: "验证错误"
        }
    )
    @action(detail=False, methods=['post'], url_path='peer-evaluation')
    def submit_peer_evaluation(self, request):
        """提交他人评价"""
        month = request.query_params.get('month')
        if not month:
            return Response(
                {'error': '必须指定评价月份'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            month_date = datetime.strptime(month, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': '月份格式错误，请使用YYYY-MM-DD格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PeerEvaluationCreateSerializer(
            data=request.data, 
            context={'request': request, 'month': month_date}
        )
        if serializer.is_valid():
            with transaction.atomic():
                peer_evaluation = serializer.save()
                return Response(
                    PeerEvaluationSerializer(peer_evaluation, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='patch',
        operation_description="管理员提交最终评价",
        request_body=AdminFinalEvaluationSerializer,
        responses={
            200: MonthlyEvaluationSerializer,
            400: "验证错误",
            403: "权限不足",
            404: "评价不存在"
        }
    )
    @action(detail=True, methods=['patch'], url_path='admin-evaluation')
    def submit_admin_evaluation(self, request, pk=None):
        """管理员提交最终评价"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能提交最终评价'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            evaluation = self.get_object()
        except MonthlyEvaluation.DoesNotExist:
            return Response(
                {'error': '月度评价不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AdminFinalEvaluationSerializer(
            evaluation, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            with transaction.atomic():
                updated_evaluation = serializer.save()
                
                # 触发绩效分值重新计算
                self._trigger_performance_recalculation(updated_evaluation)
                
                return Response(
                    MonthlyEvaluationSerializer(updated_evaluation, context={'request': request}).data
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='get',
        operation_description="获取月度评价汇总",
        manual_parameters=[
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="月份 (YYYY-MM-DD格式)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=True
            )
        ],
        responses={
            200: MonthlyEvaluationSummarySerializer(many=True),
            400: "参数错误"
        }
    )
    @action(detail=False, methods=['get'], url_path='summary')
    def get_evaluation_summary(self, request):
        """获取月度评价汇总"""
        month = request.query_params.get('month')
        if not month:
            return Response(
                {'error': '必须指定月份'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            month_date = datetime.strptime(month, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': '月份格式错误，请使用YYYY-MM-DD格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取所有活跃用户
        users = User.objects.filter(is_active=True).order_by('name')
        summary_data = []
        
        for user in users:
            # 获取用户的月度评价
            evaluation = MonthlyEvaluation.objects.filter(
                user=user,
                month=month_date
            ).first()
            
            # 计算他人评价统计
            peer_evaluations = PeerEvaluation.objects.filter(
                monthly_evaluation__user=user,
                monthly_evaluation__month=month_date
            )
            
            peer_stats = peer_evaluations.aggregate(
                count=Count('id'),
                avg_score=Avg('score'),
                avg_ranking=Avg('ranking')
            )
            
            summary_data.append({
                'user': user,
                'month': month_date,
                'self_evaluation_completed': evaluation is not None,
                'peer_evaluation_count': peer_stats['count'] or 0,
                'admin_evaluation_completed': evaluation and evaluation.admin_final_score is not None,
                'average_peer_score': peer_stats['avg_score'],
                'average_peer_ranking': peer_stats['avg_ranking']
            })
        
        serializer = MonthlyEvaluationSummarySerializer(summary_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-evaluation')
    def get_my_evaluation(self, request):
        """获取当前用户的月度评价"""
        month = request.query_params.get('month')
        if not month:
            return Response(
                {'error': '必须指定月份'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            month_date = datetime.strptime(month, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': '月份格式错误，请使用YYYY-MM-DD格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluation = MonthlyEvaluation.objects.filter(
            user=request.user,
            month=month_date
        ).first()
        
        if not evaluation:
            return Response(
                {'message': '尚未提交该月度的自我评价'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MonthlyEvaluationSerializer(evaluation, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='team-members')
    def get_team_members(self, request):
        """获取可评价的团队成员列表（除自己外）"""
        team_members = User.objects.filter(
            is_active=True
        ).exclude(id=request.user.id).order_by('name')
        
        from .serializers import UserBasicSerializer
        serializer = UserBasicSerializer(team_members, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='peer-evaluations')
    def get_peer_evaluations(self, request):
        """获取他人评价列表"""
        month = request.query_params.get('month')
        evaluee_id = request.query_params.get('evaluee')
        
        queryset = PeerEvaluation.objects.all()
        
        if month:
            queryset = queryset.filter(monthly_evaluation__month=month)
        if evaluee_id:
            queryset = queryset.filter(monthly_evaluation__user_id=evaluee_id)
        
        # 非管理员只能查看自己给出的评价
        if request.user.role != 'admin':
            queryset = queryset.filter(evaluator=request.user)
        
        peer_evaluations = queryset.select_related(
            'evaluator', 'monthly_evaluation__user'
        ).order_by('-created_at')
        
        serializer = PeerEvaluationSerializer(peer_evaluations, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description="管理员查看所有成员月度评价详情",
        manual_parameters=[
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="月份 (YYYY-MM-DD格式)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=True
            )
        ],
        responses={
            200: MonthlyEvaluationSerializer(many=True),
            403: "权限不足",
            400: "参数错误"
        }
    )
    @action(detail=False, methods=['get'], url_path='admin-view-all')
    def admin_view_all_evaluations(self, request):
        """管理员查看所有成员的月度评价详情"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能查看所有成员评价'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        month = request.query_params.get('month')
        if not month:
            return Response(
                {'error': '必须指定月份'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            month_date = datetime.strptime(month, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': '月份格式错误，请使用YYYY-MM-DD格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取所有活跃用户的月度评价
        evaluations = MonthlyEvaluation.objects.filter(
            month=month_date,
            user__is_active=True
        ).select_related('user', 'admin_evaluated_by').prefetch_related(
            'peer_evaluations__evaluator'
        ).order_by('user__name')
        
        serializer = MonthlyEvaluationSerializer(evaluations, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description="获取管理员评价历史记录",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="用户ID",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            ),
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="月份 (YYYY-MM-DD格式)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            200: AdminEvaluationHistorySerializer(many=True),
            403: "权限不足"
        }
    )
    @action(detail=False, methods=['get'], url_path='admin-history')
    def get_admin_evaluation_history(self, request):
        """获取管理员评价历史记录"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能查看评价历史'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = AdminEvaluationHistory.objects.all()
        
        # 过滤参数
        user_id = request.query_params.get('user_id')
        month = request.query_params.get('month')
        
        if user_id:
            queryset = queryset.filter(monthly_evaluation__user_id=user_id)
        if month:
            try:
                from datetime import datetime
                month_date = datetime.strptime(month, '%Y-%m-%d').date()
                queryset = queryset.filter(monthly_evaluation__month=month_date)
            except ValueError:
                return Response(
                    {'error': '月份格式错误，请使用YYYY-MM-DD格式'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        history = queryset.select_related(
            'admin_user', 'monthly_evaluation__user'
        ).order_by('-created_at')
        
        serializer = AdminEvaluationHistorySerializer(history, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='post',
        operation_description="批量提交管理员最终评价",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'evaluations': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'evaluation_id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                            'admin_final_score': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, maximum=10),
                            'admin_final_comment': openapi.Schema(type=openapi.TYPE_STRING)
                        },
                        required=['evaluation_id', 'admin_final_score']
                    )
                )
            },
            required=['evaluations']
        ),
        responses={
            200: "批量评价成功",
            400: "验证错误",
            403: "权限不足"
        }
    )
    @action(detail=False, methods=['post'], url_path='batch-admin-evaluation')
    def batch_admin_evaluation(self, request):
        """批量提交管理员最终评价"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能提交最终评价'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        evaluations_data = request.data.get('evaluations', [])
        if not evaluations_data:
            return Response(
                {'error': '评价数据不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        errors = []
        
        with transaction.atomic():
            for eval_data in evaluations_data:
                try:
                    evaluation_id = eval_data.get('evaluation_id')
                    evaluation = MonthlyEvaluation.objects.get(id=evaluation_id)
                    
                    serializer = AdminFinalEvaluationSerializer(
                        evaluation,
                        data=eval_data,
                        partial=True,
                        context={'request': request}
                    )
                    
                    if serializer.is_valid():
                        updated_evaluation = serializer.save()
                        
                        # 触发绩效分值重新计算
                        self._trigger_performance_recalculation(updated_evaluation)
                        
                        results.append({
                            'evaluation_id': evaluation_id,
                            'user': updated_evaluation.user.name,
                            'status': 'success'
                        })
                    else:
                        errors.append({
                            'evaluation_id': evaluation_id,
                            'errors': serializer.errors
                        })
                        
                except MonthlyEvaluation.DoesNotExist:
                    errors.append({
                        'evaluation_id': evaluation_id,
                        'errors': {'evaluation': '月度评价不存在'}
                    })
                except Exception as e:
                    errors.append({
                        'evaluation_id': evaluation_id,
                        'errors': {'general': str(e)}
                    })
        
        return Response({
            'success_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors
        })
    
    def _trigger_performance_recalculation(self, evaluation):
        """触发绩效分值重新计算"""
        # 实现绩效分值重新计算的逻辑
        try:
            # 获取或创建该用户该月份的绩效分值记录
            performance_score, created = PerformanceScore.objects.get_or_create(
                user=evaluation.user,
                month=evaluation.month,
                defaults={
                    'work_hours': Decimal('0.00'),
                    'work_hours_score': Decimal('0.00'),
                    'completion_rate': Decimal('0.00'),
                    'completion_rate_score': Decimal('0.00'),
                    'avg_difficulty_score': Decimal('0.00'),
                    'total_revenue': Decimal('0.00'),
                    'revenue_score': Decimal('0.00'),
                    'department_avg_score': Decimal('0.00'),
                    'task_rating_score': Decimal('0.00'),
                    'culture_understanding_score': Decimal('0.00'),
                    'team_fit_score': Decimal('0.00'),
                    'monthly_growth_score': Decimal('0.00'),
                    'biggest_contribution_score': Decimal('0.00'),
                    'peer_evaluation_score': Decimal('0.00'),
                    'admin_final_score': Decimal('0.00'),
                    'final_score': Decimal('0.00'),
                    'rank': 0
                }
            )
            
            # 更新管理员最终评分
            if evaluation.admin_final_score is not None:
                performance_score.admin_final_score = Decimal(str(evaluation.admin_final_score))
            
            # 重新计算最终分值（这里是简化版本，实际应该包含所有维度的计算）
            # 根据设计文档中的权重公式计算
            final_score = (
                performance_score.work_hours_score * Decimal('0.10') +
                performance_score.completion_rate_score * Decimal('0.15') +
                performance_score.avg_difficulty_score * Decimal('0.10') +
                performance_score.revenue_score * Decimal('0.10') +
                performance_score.department_avg_score * Decimal('0.05') +
                performance_score.task_rating_score * Decimal('0.10') +
                Decimal(str(evaluation.culture_understanding_score)) * Decimal('0.05') +
                performance_score.team_fit_score * Decimal('0.03') +
                Decimal(str(evaluation.monthly_growth_score)) * Decimal('0.03') +
                Decimal(str(evaluation.biggest_contribution_score)) * Decimal('0.04') +
                performance_score.peer_evaluation_score * Decimal('0.05') +
                performance_score.admin_final_score * Decimal('0.15')
            )
            
            performance_score.final_score = final_score.quantize(Decimal('0.01'))
            performance_score.culture_understanding_score = Decimal(str(evaluation.culture_understanding_score))
            performance_score.monthly_growth_score = Decimal(str(evaluation.monthly_growth_score))
            performance_score.biggest_contribution_score = Decimal(str(evaluation.biggest_contribution_score))
            performance_score.save()
            
            # 重新计算排名
            self._recalculate_rankings(evaluation.month)
            
        except Exception as e:
            # 记录错误但不阻止主流程
            print(f"Performance recalculation error: {e}")
    
    def _recalculate_rankings(self, month):
        """重新计算该月份所有用户的排名"""
        try:
            # 获取该月份所有绩效分值记录，按分值降序排列
            performance_scores = PerformanceScore.objects.filter(
                month=month
            ).order_by('-final_score', 'user__name')  # 分值相同时按姓名排序保证稳定性
            
            # 更新排名
            for index, score in enumerate(performance_scores, 1):
                score.rank = index
                score.save(update_fields=['rank'])
                
        except Exception as e:
            print(f"Ranking recalculation error: {e}")


class WorkHoursViewSet(viewsets.ModelViewSet):
    """工作小时视图集"""
    serializer_class = WorkHoursSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = WorkHours.objects.all()
        
        # 过滤参数
        month = self.request.query_params.get('month')
        user_id = self.request.query_params.get('user')
        
        if month:
            queryset = queryset.filter(month=month)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 非管理员只能查看自己的工作小时
        if self.request.user.role != 'admin':
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user', 'recorded_by').order_by('-month', 'user__name')
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return WorkHoursCreateSerializer
        return WorkHoursSerializer
    
    def create(self, request, *args, **kwargs):
        """创建工作小时记录（仅管理员）"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能录入工作小时'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """更新工作小时记录（仅管理员）"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能修改工作小时'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """删除工作小时记录（仅管理员）"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员才能删除工作小时'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
