"""
Content moderation for Xeinst Reddit Bot
Handles rule checking, toxicity filtering, and safety guardrails
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ContentModerator:
    """Content moderation and safety checking"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.moderation_config = config.get('moderation', {})
        self.safety_config = config.get('safety', {})
        
        # Load blacklisted words
        self.blacklisted_words = set(
            word.lower() for word in self.moderation_config.get('blacklisted_words', [])
        )
        
        # Load additional safety patterns
        self.suspicious_patterns = [
            r'\b(?:click\s+here|buy\s+now|limited\s+time|act\s+fast)\b',
            r'\b(?:don\'t\s+miss\s+out|exclusive\s+offer|special\s+deal)\b',
            r'\b(?:guaranteed|100%\s+free|no\s+risk|instant\s+results)\b',
            r'\b(?:make\s+money\s+fast|get\s+rich\s+quick|easy\s+money)\b',
            r'\b(?:work\s+from\s+home|earn\s+\$\d+/\s*day|passive\s+income)\b'
        ]
        
        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def check_content_compliance(self, 
                               content: str, 
                               subreddit: str, 
                               post_data: Dict[str, Any],
                               config: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive content compliance check"""
        
        violations = []
        recommendations = []
        required_disclosures = []
        
        # Check content length
        word_count = len(content.split())
        length_limits = config.get('content_length_limits', {})
        max_length = length_limits.get('default', 120)
        min_length = length_limits.get('min', 20)
        
        if word_count > max_length:
            violations.append(f"Content exceeds {max_length} word limit ({word_count} words)")
            recommendations.append(f"Reduce content to {max_length} words or less")
        
        if word_count < min_length:
            violations.append(f"Content too short ({word_count} words)")
            recommendations.append(f"Increase content to at least {min_length} words")
        
        # Check for toxicity and spam indicators
        toxicity_check = self.check_toxicity(content)
        if not toxicity_check['safe']:
            violations.extend(toxicity_check['issues'])
            recommendations.extend(toxicity_check['recommendations'])
        
        # Check for repetition
        repetition_check = self.check_repetition(content)
        if not repetition_check['safe']:
            violations.append("High repetition detected")
            recommendations.append("Reduce repetitive language")
        
        # Check for appropriate hashtags (if applicable)
        hashtag_check = self.check_hashtags(content, subreddit)
        if not hashtag_check['appropriate']:
            violations.append("Inappropriate or missing hashtags")
            recommendations.append("Add relevant, appropriate hashtags")
        
        # Check for required legal disclosures
        disclosure_check = self.check_required_disclosures(content, subreddit)
        if not disclosure_check['has_required']:
            violations.append("Missing required legal disclosures")
            required_disclosures.extend(disclosure_check['required'])
            recommendations.append("Add required legal disclosures")
        
        # Check for misleading claims
        misleading_check = self.check_misleading_claims(content)
        if not misleading_check['safe']:
            violations.append("Contains potentially misleading claims")
            recommendations.append("Remove or qualify misleading claims")
        
        # Check FTC compliance
        ftc_check = self.check_ftc_compliance(content)
        if not ftc_check['compliant']:
            violations.append("FTC compliance issues detected")
            recommendations.extend(ftc_check['recommendations'])
        
        # Check platform-specific compliance
        platform_check = self.check_platform_compliance(content, subreddit, post_data)
        if not platform_check['compliant']:
            violations.extend(platform_check['violations'])
            recommendations.extend(platform_check['recommendations'])
        
        # Check for spam indicators
        spam_check = self.check_spam_indicators(content)
        if not spam_check['safe']:
            violations.append("Spam indicators detected")
            recommendations.extend(spam_check['recommendations'])
        
        # Determine overall compliance
        is_compliant = len(violations) == 0
        
        return {
            'isCompliant': is_compliant,
            'violations': violations,
            'recommendations': recommendations,
            'requiredDisclosures': required_disclosures,
            'contentLength': word_count,
            'toxicityScore': toxicity_check.get('score', 0),
            'repetitionScore': repetition_check.get('score', 0),
            'spamScore': spam_check.get('score', 0)
        }
    
    def check_toxicity(self, content: str) -> Dict[str, Any]:
        """Check content for toxic language and patterns"""
        issues = []
        recommendations = []
        
        # Check for blacklisted words
        content_lower = content.lower()
        for word in self.blacklisted_words:
            if word in content_lower:
                issues.append(f"Contains blacklisted word: {word}")
                recommendations.append(f"Remove or replace '{word}'")
        
        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                issues.append("Contains suspicious marketing language")
                recommendations.append("Remove promotional language")
                break
        
        # Check for excessive capitalization
        caps_count = sum(1 for c in content if c.isupper())
        if caps_count > len(content) * 0.3:
            issues.append("Excessive capitalization detected")
            recommendations.append("Reduce use of ALL CAPS")
        
        # Check for excessive punctuation
        if content.count('!') > 3:
            issues.append("Too many exclamation marks")
            recommendations.append("Reduce exclamation marks")
        
        if content.count('?') > 5:
            issues.append("Too many question marks")
            recommendations.append("Reduce question marks")
        
        # Check for aggressive language
        aggressive_words = ['hate', 'stupid', 'idiot', 'terrible', 'awful', 'worst']
        aggressive_count = sum(1 for word in aggressive_words if word in content_lower)
        if aggressive_count > 2:
            issues.append("Contains aggressive language")
            recommendations.append("Use more neutral, respectful language")
        
        # Calculate toxicity score
        score = max(0, 10 - len(issues) * 2)
        
        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'score': score
        }
    
    def check_repetition(self, content: str) -> Dict[str, Any]:
        """Check for excessive repetition in content"""
        words = content.split()
        if len(words) == 0:
            return {'safe': True, 'score': 10}
        
        # Check word repetition
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            if len(word_lower) > 3:  # Only count words longer than 3 characters
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # Check for excessive repetition
        max_repetition = max(word_counts.values()) if word_counts else 0
        repetition_ratio = max_repetition / len(words)
        
        # Check for phrase repetition
        phrases = []
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3]).lower()
            phrases.append(phrase)
        
        phrase_counts = {}
        for phrase in phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        max_phrase_repetition = max(phrase_counts.values()) if phrase_counts else 0
        
        issues = []
        recommendations = []
        
        if repetition_ratio > 0.15:  # More than 15% repetition
            issues.append("High word repetition detected")
            recommendations.append("Vary word choice to reduce repetition")
        
        if max_phrase_repetition > 2:
            issues.append("Phrase repetition detected")
            recommendations.append("Avoid repeating the same phrases")
        
        # Calculate repetition score
        score = max(0, 10 - len(issues) * 3)
        
        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'score': score,
            'word_repetition_ratio': repetition_ratio,
            'max_phrase_repetition': max_phrase_repetition
        }
    
    def check_hashtags(self, content: str, subreddit: str) -> Dict[str, Any]:
        """Check hashtag appropriateness for subreddit"""
        # Reddit generally doesn't use hashtags, so this is more about checking
        # if hashtags are present and appropriate
        
        hashtags = re.findall(r'#\w+', content)
        
        if not hashtags:
            return {'appropriate': True, 'hashtags': []}
        
        # Check hashtag length and content
        inappropriate_hashtags = []
        for hashtag in hashtags:
            if len(hashtag) > 20:
                inappropriate_hashtags.append(hashtag)
            elif any(word in hashtag.lower() for word in ['spam', 'scam', 'money', 'rich']):
                inappropriate_hashtags.append(hashtag)
        
        return {
            'appropriate': len(inappropriate_hashtags) == 0,
            'hashtags': hashtags,
            'inappropriate': inappropriate_hashtags
        }
    
    def check_required_disclosures(self, content: str, subreddit: str) -> Dict[str, Any]:
        """Check for required legal disclosures"""
        required_disclosures = []
        
        # Check for affiliate disclosure
        if any(word in content.lower() for word in ['affiliate', 'commission', 'referral']):
            if 'affiliate disclosure' not in content.lower():
                required_disclosures.append("Affiliate disclosure required")
        
        # Check for sponsored content disclosure
        if any(word in content.lower() for word in ['sponsored', 'paid', 'advertisement']):
            if 'sponsored' not in content.lower():
                required_disclosures.append("Sponsored content disclosure required")
        
        # Check for AI-generated content disclosure
        if 'ai' in content.lower() or 'automated' in content.lower():
            if 'ai-generated' not in content.lower() and 'automated' not in content.lower():
                required_disclosures.append("AI-generated content disclosure recommended")
        
        return {
            'has_required': len(required_disclosures) == 0,
            'required': required_disclosures
        }
    
    def check_misleading_claims(self, content: str) -> Dict[str, Any]:
        """Check for potentially misleading claims"""
        misleading_patterns = [
            r'\b(?:guaranteed|100%\s+guaranteed|money\s+back\s+guarantee)\b',
            r'\b(?:instant\s+results|overnight\s+success|get\s+rich\s+quick)\b',
            r'\b(?:no\s+risk|risk\s+free|zero\s+risk)\b',
            r'\b(?:everyone\s+can|anyone\s+can|works\s+for\s+everyone)\b',
            r'\b(?:best\s+in\s+the\s+world|number\s+one|top\s+rated)\b'
        ]
        
        issues = []
        for pattern in misleading_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Contains potentially misleading claim: {pattern}")
        
        return {
            'safe': len(issues) == 0,
            'issues': issues
        }
    
    def check_ftc_compliance(self, content: str) -> Dict[str, Any]:
        """Check FTC compliance requirements"""
        recommendations = []
        
        # Check for endorsement disclosure
        if any(word in content.lower() for word in ['endorsement', 'testimonial', 'review']):
            if 'disclosure' not in content.lower():
                recommendations.append("Add endorsement disclosure")
        
        # Check for affiliate disclosure
        if any(word in content.lower() for word in ['affiliate', 'commission', 'referral']):
            if 'affiliate disclosure' not in content.lower():
                recommendations.append("Add affiliate disclosure")
        
        # Check for sponsored content
        if any(word in content.lower() for word in ['sponsored', 'paid', 'advertisement']):
            if 'sponsored' not in content.lower():
                recommendations.append("Add sponsored content disclosure")
        
        return {
            'compliant': len(recommendations) == 0,
            'recommendations': recommendations
        }
    
    def check_platform_compliance(self, content: str, subreddit: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check platform-specific compliance rules"""
        violations = []
        recommendations = []
        
        # Check for subreddit-specific rules
        if subreddit.lower() == 'entrepreneur':
            if 'self-promotion' in content.lower() and 'xeinst' in content.lower():
                violations.append("Self-promotion not allowed in r/Entrepreneur")
                recommendations.append("Remove promotional content")
        
        # Check for Reddit-wide rules
        if 'vote manipulation' in content.lower():
            violations.append("Vote manipulation not allowed")
            recommendations.append("Remove vote manipulation language")
        
        if 'harassment' in content.lower():
            violations.append("Harassment not allowed")
            recommendations.append("Remove harassing language")
        
        # Check for link compliance
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        for link in links:
            if not any(domain in link for domain in ['reddit.com', 'xeinst.com']):
                violations.append("External links may not be allowed")
                recommendations.append("Check subreddit rules for external links")
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'recommendations': recommendations
        }
    
    def check_spam_indicators(self, content: str) -> Dict[str, Any]:
        """Check for spam indicators"""
        issues = []
        recommendations = []
        
        # Check for excessive links
        links = re.findall(r'http[s]?://', content)
        if len(links) > 2:
            issues.append("Too many links")
            recommendations.append("Reduce number of links")
        
        # Check for excessive mentions
        mentions = re.findall(r'@\w+', content)
        if len(mentions) > 3:
            issues.append("Too many user mentions")
            recommendations.append("Reduce number of user mentions")
        
        # Check for repetitive patterns
        if content.count('!') > 3:
            issues.append("Excessive exclamation marks")
            recommendations.append("Reduce exclamation marks")
        
        # Check for suspicious language patterns
        suspicious_phrases = [
            'click here', 'buy now', 'limited time', 'act fast',
            'don\'t miss out', 'exclusive offer', 'special deal'
        ]
        
        for phrase in suspicious_phrases:
            if phrase in content.lower():
                issues.append(f"Contains suspicious phrase: {phrase}")
                recommendations.append(f"Remove or rephrase '{phrase}'")
        
        # Calculate spam score
        score = max(0, 10 - len(issues) * 2)
        
        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'score': score
        }
    
    def check_rate_limits(self, 
                         subreddit: str, 
                         action_type: str, 
                         database) -> Dict[str, Any]:
        """Check if action is allowed based on rate limits"""
        
        # Get rate limit configuration
        rate_limits = self.config.get('rate_limits', {})
        global_cooldown = rate_limits.get('global_cooldown_min', 90)
        sub_cooldown = rate_limits.get('sub_cooldown_hours', 12)
        max_posts_per_day = rate_limits.get('max_posts_per_day', 10)
        max_comments_per_day = rate_limits.get('max_comments_per_day', 50)
        
        # Check global rate limit
        if not database.check_rate_limit('global', 'global', 1, global_cooldown):
            return {
                'allowed': False,
                'reason': f"Global rate limit: {global_cooldown} seconds between actions",
                'wait_time': global_cooldown
            }
        
        # Check subreddit-specific rate limit
        if action_type == 'post':
            if not database.check_rate_limit('subreddit', subreddit, 1, sub_cooldown * 60):
                return {
                    'allowed': False,
                    'reason': f"Subreddit rate limit: {sub_cooldown} hours between posts",
                    'wait_time': sub_cooldown * 3600
                }
        
        # Check daily limits
        today = datetime.now().strftime('%Y-%m-%d')
        
        if action_type == 'post':
            daily_posts = database.get_daily_stats(today).get('posts_made', 0)
            if daily_posts >= max_posts_per_day:
                return {
                    'allowed': False,
                    'reason': f"Daily post limit reached: {max_posts_per_day}",
                    'wait_time': 86400  # 24 hours
                }
        
        elif action_type == 'comment':
            daily_comments = database.get_daily_stats(today).get('comments_made', 0)
            if daily_comments >= max_comments_per_day:
                return {
                    'allowed': False,
                    'reason': f"Daily comment limit reached: {max_comments_per_day}",
                    'wait_time': 86400  # 24 hours
                }
        
        return {
            'allowed': True,
            'reason': "Rate limits satisfied"
        }
    
    def check_subreddit_rules(self, content: str, subreddit: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if content complies with subreddit rules"""
        
        # Check for "No self-promo" flairs
        if post_data.get('flair') and 'no self-promo' in post_data['flair'].lower():
            if 'xeinst' in content.lower():
                return {
                    'compliant': False,
                    'violation': "Post has 'No self-promo' flair",
                    'recommendation': "Do not mention Xeinst in this thread"
                }
        
        # Check for subreddit-specific content restrictions
        if subreddit.lower() in ['entrepreneur', 'startups']:
            if 'self-promotion' in content.lower() and 'xeinst' in content.lower():
                return {
                    'compliant': False,
                    'violation': "Self-promotion not allowed in this subreddit",
                    'recommendation': "Remove promotional content"
                }
        
        return {
            'compliant': True,
            'violation': None,
            'recommendation': None
        }
    
    def get_compliance_recommendations(self, violations: List[str]) -> List[str]:
        """Get specific recommendations for compliance violations"""
        recommendations = []
        
        for violation in violations:
            if 'length' in violation.lower():
                recommendations.append("Reduce content length to meet requirements")
            elif 'toxicity' in violation.lower():
                recommendations.append("Review and remove toxic language")
            elif 'repetition' in violation.lower():
                recommendations.append("Vary word choice and reduce repetition")
            elif 'disclosure' in violation.lower():
                recommendations.append("Add required legal disclosures")
            elif 'misleading' in violation.lower():
                recommendations.append("Qualify or remove misleading claims")
            elif 'spam' in violation.lower():
                recommendations.append("Remove spam indicators and promotional language")
            else:
                recommendations.append("Review content for compliance issues")
        
        return recommendations
    
    def log_compliance_activity(self, 
                               action: str, 
                               content: str, 
                               subreddit: str, 
                               compliance_result: Dict[str, Any],
                               database) -> None:
        """Log compliance checking activity"""
        try:
            # This would typically log to a database or file
            logger.info(f"Compliance check for {action} in r/{subreddit}: "
                       f"Compliant={compliance_result['isCompliant']}, "
                       f"Violations={len(compliance_result['violations'])}")
            
        except Exception as e:
            logger.error(f"Error logging compliance activity: {e}")
    
    def get_compliance_report(self, 
                            content: str, 
                            subreddit: str, 
                            post_data: Dict[str, Any],
                            config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        compliance_result = self.check_content_compliance(content, subreddit, post_data, config)
        
        # Add additional metadata
        report = {
            **compliance_result,
            'timestamp': datetime.now().isoformat(),
            'subreddit': subreddit,
            'content_length': len(content.split()),
            'compliance_score': self._calculate_compliance_score(compliance_result),
            'risk_level': self._assess_risk_level(compliance_result),
            'action_required': len(compliance_result['violations']) > 0
        }
        
        return report
    
    def _calculate_compliance_score(self, compliance_result: Dict[str, Any]) -> int:
        """Calculate overall compliance score (0-100)"""
        base_score = 100
        
        # Deduct points for violations
        violation_penalty = len(compliance_result['violations']) * 15
        
        # Deduct points for low scores
        score_penalty = 0
        if 'toxicityScore' in compliance_result:
            score_penalty += (10 - compliance_result['toxicityScore']) * 2
        if 'repetitionScore' in compliance_result:
            score_penalty += (10 - compliance_result['repetitionScore']) * 2
        if 'spamScore' in compliance_result:
            score_penalty += (10 - compliance_result['spamScore']) * 2
        
        final_score = max(0, base_score - violation_penalty - score_penalty)
        return final_score
    
    def _assess_risk_level(self, compliance_result: Dict[str, Any]) -> str:
        """Assess overall risk level"""
        score = self._calculate_compliance_score(compliance_result)
        
        if score >= 90:
            return "LOW"
        elif score >= 70:
            return "MEDIUM"
        elif score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"
